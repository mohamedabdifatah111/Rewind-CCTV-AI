import axios from 'axios';

/**
 * EXPECTED BACKEND CONTRACT (edit `endpoints` and the normalize* functions below if yours differs).
 * Every timestamp is in SECONDS.
 *
 * GET    /health/                  -> { status: "ok" }
 * GET    /config/                  -> { max_upload_size_mb, supported_formats: ["mp4","mov","avi"], app_version?, retention_days?, model? }
 * GET    /dashboard/stats/         -> { total_videos, processed_videos, processing_videos, failed_videos, recent_videos: [Video], recent_searches: [{id, query, video_title?, result_count, created_at}] }
 * GET    /videos/?page&page_size&search&status -> { count, results: [Video] }
 * POST   /videos/                  (multipart, field "file", optional "title") -> Video
 * GET    /videos/:id/              -> Video + { analysis: [{timestamp_seconds, description}], frames_extracted }
 * DELETE /videos/:id/              -> 204
 * POST   /search/                  { query, video_id? } -> { results: [{video_id, video_title, timestamp_seconds, description}] }
 * GET    /jobs/                    -> { count, results: [Job] } (or plain array)
 * Video: { id, title, uploaded_at, duration_seconds, status: pending|processing|completed|failed, progress (0-100), file_size, file_url, thumbnail_url, frames_processed, error }
 * Job:   { id, video_id, video_title, status, started_at, completed_at, frames_processed, error }
 */
export const endpoints = {
  health: '/health/', config: '/config/', stats: '/dashboard/stats/',
  videos: '/videos/', video: (id) => `/videos/${id}/`,
  search: '/search/', jobs: '/jobs/',
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const client = axios.create({ baseURL: API_BASE_URL, timeout: 30000 });

/** Turn any Axios failure into a message the UI can show. */
export function parseError(err) {
  if (axios.isCancel(err)) return { kind: 'cancelled', message: 'Request cancelled.' };
  if (err.code === 'ECONNABORTED') return { kind: 'timeout', message: 'The server took too long to respond. Try again.' };
  if (!err.response) return { kind: 'network', message: `Cannot reach the backend at ${API_BASE_URL}. Check that it is running and that CORS allows this origin.` };
  const { status, data } = err.response;
  const detail = typeof data === 'string' ? '' : data?.detail || data?.error || data?.message
    || (data && typeof data === 'object' ? Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(', ')}`).join('; ') : '');
  const map = { 400: 'The request was invalid.', 401: 'You need to sign in.', 403: 'You do not have permission for this action.', 404: 'Not found.' };
  const message = detail || map[status] || (status >= 500 ? 'The server hit an error. Try again shortly.' : `Request failed (${status}).`);
  return { kind: status >= 500 ? 'server' : 'http', status, message };
}
const call = async (fn) => { try { return (await fn()).data; } catch (e) { throw parseError(e); } };

const normalizeVideo = (v = {}) => ({
  id: v.id, title: v.title || v.name || v.filename || `Video ${v.id}`,
  uploadedAt: v.uploaded_at || v.created_at, duration: v.duration_seconds ?? v.duration ?? null,
  status: v.status || 'pending', progress: v.progress ?? null, size: v.file_size ?? v.size ?? null,
  url: v.file_url || v.video_url || v.file || null, thumbnail: v.thumbnail_url || v.thumbnail || null,
  framesProcessed: v.frames_processed ?? v.frames_extracted ?? null, error: v.error || v.error_message || null,
  analysis: (v.analysis || v.activities || []).map((a) => ({ time: Number(a.timestamp_seconds ?? a.timestamp ?? a.time), description: a.description })),
});
const normalizeJob = (j = {}) => ({
  id: j.id, videoId: j.video_id ?? j.video, title: j.video_title || j.video_name || `Video ${j.video_id ?? j.video}`,
  status: j.status, startedAt: j.started_at, completedAt: j.completed_at,
  frames: j.frames_processed ?? null, error: j.error || j.error_message || null,
});
const list = (d, fn) => { const arr = Array.isArray(d) ? d : d?.results || []; return { count: d?.count ?? arr.length, results: arr.map(fn) }; };

export const videosApi = {
  list: (params, signal) => call(() => client.get(endpoints.videos, { params, signal })).then((d) => list(d, normalizeVideo)),
  get: (id, signal) => call(() => client.get(endpoints.video(id), { signal })).then(normalizeVideo),
  remove: (id) => call(() => client.delete(endpoints.video(id))),
};
export const uploadsApi = {
  upload: (file, { onProgress, signal } = {}) => {
    const fd = new FormData(); fd.append('file', file); fd.append('title', file.name);
    return call(() => client.post(endpoints.videos, fd, {
      signal, timeout: 0, // large uploads: no client timeout
      onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
    })).then(normalizeVideo);
  },
};
export const searchApi = {
  query: (query, videoId, signal) => call(() => client.post(endpoints.search, { query, ...(videoId ? { video_id: videoId } : {}) }, { signal, timeout: 120000 }))
    .then((d) => (Array.isArray(d) ? d : d?.results || []).map((r) => ({
      videoId: r.video_id ?? r.video, title: r.video_title || r.video_name, time: Number(r.timestamp_seconds ?? r.timestamp), description: r.description,
    }))),
};
export const jobsApi = { list: (signal) => call(() => client.get(endpoints.jobs, { signal })).then((d) => list(d, normalizeJob)) };
export const dashboardApi = {
  stats: (signal) => call(() => client.get(endpoints.stats, { signal })).then((d) => ({
    total: d.total_videos, processed: d.processed_videos, processing: d.processing_videos, failed: d.failed_videos,
    recentVideos: (d.recent_videos || []).map(normalizeVideo),
    recentSearches: (d.recent_searches || []).map((s) => ({ id: s.id, query: s.query, title: s.video_title, count: s.result_count, at: s.created_at })),
  })),
};
export const systemApi = {
  health: () => call(() => client.get(endpoints.health, { timeout: 8000 })),
  config: () => call(() => client.get(endpoints.config)).then((d) => ({
    maxMb: d.max_upload_size_mb ?? null, formats: (d.supported_formats || []).map((f) => String(f).replace('.', '').toLowerCase()),
    version: d.app_version, retentionDays: d.retention_days, model: d.model,
  })),
};
