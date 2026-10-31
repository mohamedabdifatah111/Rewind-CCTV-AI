// All timestamps in this app are SECONDS (float) from the start of the video.
export function formatTimestamp(seconds) {
  const s = Math.max(0, Math.floor(Number(seconds) || 0));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  const mm = String(m).padStart(2, '0'), rr = String(r).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${rr}` : `${m}:${rr}`;
}
export function formatDuration(seconds) {
  return seconds == null || Number.isNaN(Number(seconds)) ? '—' : formatTimestamp(seconds);
}
export function formatBytes(bytes) {
  if (bytes == null) return '—';
  const u = ['B', 'KB', 'MB', 'GB']; let i = 0, n = Number(bytes);
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
}
export function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}
