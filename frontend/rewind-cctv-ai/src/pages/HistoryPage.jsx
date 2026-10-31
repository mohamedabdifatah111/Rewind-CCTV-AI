import { Link } from 'react-router-dom';
import { History, RefreshCw } from 'lucide-react';
import PageHeader from './PageHeader.jsx';
import ProcessingBadge from '../components/ProcessingBadge.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import LoadingSkeleton from '../components/LoadingSkeleton.jsx';
import { jobsApi } from '../services/api.js';
import { useFetch, usePolling } from '../hooks/useApi.js';
import { formatDate } from '../utils/format.js';

export default function HistoryPage() {
  const { data, error, loading, reload } = useFetch((s) => jobsApi.list(s), []);
  usePolling(reload, 5000, data?.results.some((j) => ['pending', 'processing'].includes(j.status)));
  return (
    <>
      <PageHeader title="Processing history" text="Status refreshes automatically while jobs are running.">
        <button className="btn" onClick={reload}><RefreshCw size={14} /> Refresh</button>
      </PageHeader>
      {error ? <ErrorState error={error} onRetry={reload} /> : loading && !data ? <LoadingSkeleton /> : !data.results.length ? <EmptyState icon={History} title="No processing jobs" text="Jobs appear here after you upload footage." /> : (
        <div className="panel overflow-x-auto p-4">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="text-slate-400"><tr>{['Video', 'Status', 'Started', 'Completed', 'Frames', 'Details'].map((h) => <th key={h} className="py-2 pr-4 font-medium">{h}</th>)}</tr></thead>
            <tbody>
              {data.results.map((j) => (
                <tr key={j.id} className="border-t border-line align-top">
                  <td className="py-3 pr-4">{j.videoId ? <Link className="text-accent hover:underline" to={`/library/${j.videoId}`}>{j.title}</Link> : j.title}</td>
                  <td className="pr-4"><ProcessingBadge status={j.status} /></td>
                  <td className="pr-4 text-slate-400">{formatDate(j.startedAt)}</td>
                  <td className="pr-4 text-slate-400">{formatDate(j.completedAt)}</td>
                  <td className="pr-4 font-mono text-slate-300">{j.frames ?? '—'}</td>
                  <td className="max-w-xs text-bad">{j.error || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
