import { Link } from 'react-router-dom';
import { AlertTriangle, CheckCircle2, Film, Loader2, RefreshCw, ScanSearch } from 'lucide-react';
import PageHeader from './PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import VideoTable from '../components/VideoTable.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import LoadingSkeleton from '../components/LoadingSkeleton.jsx';
import { dashboardApi } from '../services/api.js';
import { useFetch, usePolling } from '../hooks/useApi.js';
import { formatDate } from '../utils/format.js';

export default function Overview() {
  const { data, error, loading, reload } = useFetch((s) => dashboardApi.stats(s), []);
  usePolling(reload, 10000, (data?.processing ?? 0) > 0);
  return (
    <>
      <PageHeader title="Overview" text="Footage and search activity across your library.">
        <button className="btn" onClick={reload}><RefreshCw size={14} /> Refresh</button>
      </PageHeader>
      {error ? <ErrorState error={error} onRetry={reload} /> : loading && !data ? <LoadingSkeleton rows={3} className="h-24" /> : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard label="Total videos" value={data.total} icon={Film} />
            <StatCard label="Processed" value={data.processed} icon={CheckCircle2} tone="text-ok" />
            <StatCard label="Processing" value={data.processing} icon={Loader2} tone="text-accent" />
            <StatCard label="Failed" value={data.failed} icon={AlertTriangle} tone={data.failed ? 'text-bad' : 'text-slate-100'} />
          </div>
          <section className="panel p-4">
            <h2 className="mb-2 font-medium text-slate-100">Recent footage</h2>
            {data.recentVideos.length ? <VideoTable videos={data.recentVideos} /> : <EmptyState icon={Film} title="No footage yet" text="Upload a recording to start searching it." action={<Link className="btn btn-primary" to="/upload">Upload footage</Link>} />}
          </section>
          <section className="panel p-4">
            <h2 className="mb-2 font-medium text-slate-100">Recent AI searches</h2>
            {data.recentSearches.length ? (
              <ul className="divide-y divide-line text-sm">
                {data.recentSearches.map((s) => (
                  <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                    <span className="text-slate-200">“{s.query}”<span className="ml-2 text-slate-500">{s.title || 'All videos'}</span></span>
                    <span className="text-xs text-slate-400">{s.count ?? 0} matches · {formatDate(s.at)}</span>
                  </li>
                ))}
              </ul>
            ) : <EmptyState icon={ScanSearch} title="No searches yet" text="Ask a question about your footage." action={<Link className="btn btn-primary" to="/search">Open AI search</Link>} />}
          </section>
        </div>
      )}
    </>
  );
}
