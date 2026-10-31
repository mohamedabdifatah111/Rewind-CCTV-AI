import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, XCircle } from 'lucide-react';
import PageHeader from './PageHeader.jsx';
import UploadDropzone from '../components/UploadDropzone.jsx';
import UploadProgress from '../components/UploadProgress.jsx';
import ProcessingBadge from '../components/ProcessingBadge.jsx';
import { systemApi, uploadsApi, videosApi } from '../services/api.js';
import { useFetch, usePolling } from '../hooks/useApi.js';
import { formatBytes, formatDuration } from '../utils/format.js';

export default function UploadPage() {
  const { data: cfg, error: cfgError } = useFetch(() => systemApi.config(), []);
  const [file, setFile] = useState(null);
  const [percent, setPercent] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [video, setVideo] = useState(null);
  const ctrl = useRef(null);

  const formats = cfg?.formats?.length ? cfg.formats : null;
  const accept = formats ? formats.map((f) => `.${f}`).join(',') : 'video/*';

  const validate = (f) => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (formats && !formats.includes(ext)) return `.${ext} is not supported. Use: ${formats.join(', ').toUpperCase()}.`;
    if (cfg?.maxMb && f.size > cfg.maxMb * 1024 * 1024) return `File is ${formatBytes(f.size)}. The limit is ${cfg.maxMb} MB.`;
    return null;
  };
  const choose = (f) => { setVideo(null); setError(validate(f)); setFile(f); setPercent(0); };
  const start = async () => {
    if (!file || uploading) return;
    setUploading(true); setError(null); setPercent(0);
    ctrl.current = new AbortController();
    try { setVideo(await uploadsApi.upload(file, { onProgress: setPercent, signal: ctrl.current.signal })); setFile(null); }
    catch (e) { if (e.kind !== 'cancelled') setError(e.message); }
    finally { setUploading(false); }
  };
  const refresh = async () => { try { setVideo(await videosApi.get(video.id)); } catch { /* keep last known state */ } };
  usePolling(refresh, 4000, !!video && ['pending', 'processing'].includes(video.status));

  return (
    <>
      <PageHeader title="Upload footage" text="Recordings are analysed after upload. Search becomes available once processing completes." />
      <div className="max-w-2xl space-y-4">
        {cfgError && <p className="rounded-lg border border-warn/30 bg-warn/10 p-3 text-sm text-warn">Could not load upload limits ({cfgError.message}). The backend will validate the file instead.</p>}
        <UploadDropzone onFile={choose} disabled={uploading} accept={accept}
          hint={`${formats ? formats.join(', ').toUpperCase() : 'Video files'}${cfg?.maxMb ? ` · up to ${cfg.maxMb} MB` : ''}`} />
        {file && !uploading && (
          <div className="panel flex flex-wrap items-center justify-between gap-3 p-4">
            <div className="min-w-0 text-sm"><p className="truncate text-slate-100">{file.name}</p><p className="text-slate-400">{formatBytes(file.size)}</p></div>
            <div className="flex gap-2"><button className="btn" onClick={() => { setFile(null); setError(null); }}>Remove</button><button className="btn btn-primary" onClick={start} disabled={!!error}>Upload</button></div>
          </div>
        )}
        {uploading && <UploadProgress percent={percent} name={file?.name} onCancel={() => ctrl.current?.abort()} />}
        {error && <p role="alert" className="flex items-start gap-2 rounded-lg border border-bad/30 bg-bad/10 p-3 text-sm text-bad"><XCircle size={16} className="mt-0.5 shrink-0" />{error}</p>}
        {video && (
          <div className="panel space-y-3 p-4">
            <p className="flex items-center gap-2 text-sm text-ok"><CheckCircle2 size={16} /> Upload received by the backend</p>
            <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-medium text-slate-100">{video.title}</h2><ProcessingBadge status={video.status} /></div>
            <p className="text-sm text-slate-400">{formatBytes(video.size)} · {formatDuration(video.duration)}{video.progress != null && ` · ${video.progress}% analysed`}</p>
            {video.error && <p className="text-sm text-bad">{video.error}</p>}
            <Link className="btn" to={`/library/${video.id}`}>View processing details</Link>
          </div>
        )}
      </div>
    </>
  );
}
