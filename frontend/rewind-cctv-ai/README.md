# Rewind CCTV AI — Frontend

React + Vite + Tailwind interface for searching CCTV footage in natural language. Nothing is mocked: every number, video and search result comes from your backend.

## Run
```bash
npm install
cp .env.example .env     # set VITE_API_BASE_URL (default http://localhost:8000/api)
npm run dev              # http://localhost:5173
npm run build            # production build in dist/
```

## Connect to the Django backend
1. Start Django on port 8000 and expose the endpoints below under `/api/`.
2. Allow this origin: `pip install django-cors-headers`, add `corsheaders` to `INSTALLED_APPS`, `corsheaders.middleware.CorsMiddleware` at the top of `MIDDLEWARE`, and `CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]`.
3. Serve uploaded video files over HTTP with range support (Django's dev server works for `MEDIA_URL`), and return the absolute URL as `file_url`, otherwise seeking will not work.
4. If your JSON differs, edit only `src/services/api.js` (`endpoints` and the `normalize*` functions).

## Endpoints the backend must implement
| Method | Path | Returns |
|---|---|---|
| GET | `/health/` | `{status:"ok"}` |
| GET | `/config/` | `{max_upload_size_mb, supported_formats[], app_version?, retention_days?, model?}` |
| GET | `/dashboard/stats/` | `{total_videos, processed_videos, processing_videos, failed_videos, recent_videos[], recent_searches[]}` |
| GET | `/videos/?page&page_size&search&status` | `{count, results:[Video]}` |
| POST | `/videos/` | multipart `file` (+`title`) → `Video` (status must be `pending`/`processing`, never faked as complete) |
| GET | `/videos/:id/` | `Video` + `analysis:[{timestamp_seconds, description}]` |
| DELETE | `/videos/:id/` | `204` |
| POST | `/search/` | body `{query, video_id?}` → `{results:[{video_id, video_title, timestamp_seconds, description}]}` |
| GET | `/jobs/` | `{count, results:[Job]}` |

`Video`: `id, title, uploaded_at, duration_seconds, status (pending|processing|completed|failed), progress 0-100, file_size, file_url, thumbnail_url, frames_processed, error`
`Job`: `id, video_id, video_title, status, started_at, completed_at, frames_processed, error`

All timestamps are **seconds** from the start of the video. Statuses are polled every 4–10 seconds while anything is processing.

## Known gaps
- No login screen: the profile block is a placeholder until you add authentication (401/403 are already surfaced as errors).
- Upload cancellation aborts the browser request; the backend must clean up partial uploads itself.
