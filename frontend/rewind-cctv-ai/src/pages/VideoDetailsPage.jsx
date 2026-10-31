import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import PageHeader from './PageHeader.jsx';
import VideoPlayer from '../components/VideoPlayer.jsx';
import TimestampResult from '../components/TimestampResult.jsx';
import ProcessingBadge from '../components/ProcessingBadge.jsx';
import ErrorState from '../components/ErrorState.jsx';
import LoadingSkeleton from '../components/LoadingSkeleton.jsx';
import EmptyState from '../components/EmptyState.jsx';
import { videosApi } from '../services/api.js';
import { useFetch, usePolling } from '../hooks/useApi.js';
import { formatBytes, formatDate, formatDuration } from '../utils/format.js';

export default function VideoDetailsPage() {
  const { id } = useParams();
  const [seek, setSeek] = useState(null);
  const { data: v, error, loading, reload } = useFetch((s) => videosApi.get(id, s), [id]);
  usePolling(reload, 4000, !!v && ['pending', 'processing'].includes(v.status));
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!v) return <LoadingSkeleton rows={2} className="h-64" />;
  const open = (time) => setSeek({ time, nonce: Date.now() });
  return (
    <>
      <Link to="/library" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-100"><ArrowLeft size={14} /> Video library</Link>
      <PageHeader title={v.title}><ProcessingBadge status={v.status} /></PageHeader>
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <div className="space-y-4">
          <VideoPlayer src={v.url} seek={seek} />
          <dl className="panel grid grid-cols-2 gap-4 p-4 text-sm sm:grid-cols-4">
            {[['Duration', formatDuration(v.duration)], ['Uploaded', formatDate(v.uploadedAt)], ['File size', formatBytes(v.size)], ['Frames analysed', v.framesProcessed ?? '—']].map(([k, val]) => (
              <div key={k}><dt className="text-slate-500">{k}</dt><dd className="mt-0.5 text-slate-100">{val}</dd></div>
            ))}
          </dl>
          {['pending', 'processing'].includes(v.status) && (
            <div className="panel p-4" aria-live="polite">
              <p className="mb-2 text-sm text-slate-300">Analysis progress{v.progress != null ? ` · ${v.progress}%` : ''}</p>
              <div className="h-2 overflow-hidden rounded-full bg-raised"><div className="h-full bg-accent transition-[width]" style={{ width: `${v.progress ?? 5}%` }} /></div>
            </div>
          )}
          {v.status === 'failed' && <ErrorState error={{ message: v.error || 'Processing failed. The backend gave no details.' }} />}
        </div>
        <section className="panel flex max-h-[640px] flex-col p-4" aria-label="Detected activity">
          <h2 className="mb-1 font-medium text-slate-100">Activity timeline</h2>
          <p className="mb-3 text-xs text-slate-500">Descriptions come from sampled frames, so brief events between samples may be missing.</p>
          <div className="space-y-2 overflow-y-auto">
            {v.analysis.length ? v.analysis.map((a, i) => <TimestampResult key={i} time={a.time} description={a.description} onOpen={() => open(a.time)} active={seek?.time === a.time} />)
              : <EmptyState title={v.status === 'completed' ? 'No activity recorded' : 'Not analysed yet'} text={v.status === 'completed' ? 'The backend returned no frame descriptions for this video.' : 'Descriptions appear when processing completes.'} />}
          </div>
        </section>
      </div>
    </>
  );
}
