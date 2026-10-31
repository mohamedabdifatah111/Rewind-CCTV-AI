# Rewind CCTV AI — Backend

Django + DRF service that ingests CCTV recordings, samples frames with OpenCV, describes each frame with **Gemma 4 (`gemma-4-26b-a4b-it`) through the hosted Gemini API**, stores descriptions in PostgreSQL, and answers natural-language searches with timestamps (in seconds) for playback.

## Architecture
`upload → validate (ext, MIME, magic bytes, size, decode check) → save (server-chosen filename) → Video + ProcessingJob → queue → worker: probe → sample a frame every N s (in memory, JPEG, not retained) → Gemma → validated JSON → PostgreSQL → search (full-text) → timestamps → frontend seeks the original file via /api/videos/<id>/stream/`

Apps: `videos` (upload, library, streaming), `processing` (jobs, frame sampling, pipeline, Celery task), `ai_engine` (`services/gemini_service.py`), `search`, `dashboard`, `common`.

## Setup
Prerequisites: Python 3.11+, PostgreSQL 14+, FFmpeg (`ffprobe` is used to recover duration when metadata is missing), Redis (for Celery).
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in DJANGO_SECRET_KEY, DB_*, GEMINI_API_KEY
createdb rewind                 # or: CREATE DATABASE rewind; CREATE USER rewind ...
python manage.py migrate
python manage.py runserver      # http://localhost:8000/api/
celery -A config worker -l info # separate terminal, PROCESSING_MODE=celery (default)
```
No Redis yet? Set `PROCESSING_MODE=thread` (in-process thread, lost on restart) or `sync` (blocks the upload request; debugging only). Upgrade path: `thread` → `celery` is a one-line env change.

## Gemini API
Create a key in Google AI Studio and put it in `.env` as `GEMINI_API_KEY`. Model id: `gemma-4-26b-a4b-it` (`GEMMA_MODEL`). The key is only read server-side and never returned by any endpoint. Check Google's current terms: Gemini API Additional Terms of Service for the hosted API (frames you send are covered by them), and the Gemma model licence/terms published with the model. Free-tier quotas are small; a 1-hour video at a 2 s interval is 1,800 requests.
Retries: 3 with exponential backoff for 5xx/timeouts/malformed JSON; 400/401/403/404 fail immediately; a persistent 429 stops the job. A frame that keeps failing is skipped and reported on the job.

## Environment variables
See `.env.example`. Key ones: `MAX_UPLOAD_SIZE_MB`, `FRAME_INTERVAL_SECONDS` (default 2), `FRAME_MAX_SIDE_PX`, `PROCESSING_MODE`, `API_REQUIRE_AUTH`, `CORS_ALLOWED_ORIGINS`.

## Tests
```bash
DB_ENGINE=sqlite DJANGO_DEBUG=true python manage.py test      # mocked Gemini, synthetic video, no network
GEMINI_INTEGRATION_API_KEY=... python manage.py test apps.ai_engine   # optional: one real (billable) API call
```
Tests use SQLite, so PostgreSQL full-text search is not exercised by them (see Limitations).

## API (all JSON; timestamps in seconds; lists are `{count, next, previous, results}`; `?page=&page_size=`)
| Method | Path | Notes |
|---|---|---|
| POST | `/api/videos/upload/` (alias `POST /api/videos/`) | multipart `file`, optional `title` → 201 Video; 400 on bad/empty/oversized/corrupt file |
| GET | `/api/videos/` | filters `search=` (title), `status=pending\|processing\|completed\|failed` |
| GET / DELETE | `/api/videos/<id>/` | detail adds `analysis[{timestamp_seconds, description}]`; DELETE removes file, jobs, frames, descriptions (204) |
| GET | `/api/videos/<id>/stream/` | original file, HTTP Range supported |
| GET | `/api/videos/<id>/frames/` | frames with description, objects, actions |
| GET | `/api/videos/<id>/processing/` | latest job |
| GET | `/api/jobs/` | `?status=` |
| POST | `/api/search/` | `{query, video_id?}` → `{results:[{video_id, video_title, timestamp_seconds, description, relevance_score}], count, message}` |
| GET | `/api/dashboard/stats/` | totals, recent videos, recent searches |
| GET | `/api/config/`, `/api/health/` | upload limits/formats/model; liveness |

Video `status` is `pending` (stored as `uploaded`/`queued`), `processing`, `completed` or `failed`; the exact stored value is in `raw_status`. This matches the React frontend's contract.

## Privacy and limitations
- Frames are analysed in memory and **not stored**; only text descriptions are kept. Sampled frames are sent to Google's hosted API, so only upload footage you have consent to process.
- The prompt forbids identifying people or guessing intent; no face recognition. Descriptions can still be wrong: verify in the video.
- **Sparse sampling** (every 2 s by default) can miss events between samples. Audio is ignored.
- Search is **PostgreSQL keyword full-text search with stemming**, not semantic: "walked in" will not match "entered". `relevance_score` is `ts_rank/(1+ts_rank)`. On SQLite (tests only) a simpler term-overlap score is used. Adding embeddings would be a separate, explicitly documented step.
- **No user accounts yet.** Anyone who can reach the API can read/delete videos. Set `API_REQUIRE_AUTH=true` and add authentication (and an owner field on `Video`) before exposing it beyond a trusted network. Media is never served from `/media/`; it streams only through the API (which a `<video>` tag cannot authenticate with a header, so signed URLs or cookie auth are needed when you add login).
- Retention: nothing deletes data automatically; `DATA_RETENTION_DAYS` is informational until a cleanup job is added.
