import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Film } from 'lucide-react';
import PageHeader from './PageHeader.jsx';
import SearchBar from '../components/SearchBar.jsx';
import VideoCard from '../components/VideoCard.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import LoadingSkeleton from '../components/LoadingSkeleton.jsx';
import ConfirmDialog from '../components/ConfirmDialog.jsx';
import { videosApi } from '../services/api.js';
import { useFetch } from '../hooks/useApi.js';

const PAGE_SIZE = 12;
export default function LibraryPage() {
  const [q, setQ] = useState('');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [target, setTarget] = useState(null);
  const [busy, setBusy] = useState(false);
  const [delError, setDelError] = useState(null);

  useEffect(() => { const t = setTimeout(() => { setSearch(q.trim()); setPage(1); }, 350); return () => clearTimeout(t); }, [q]);
  const { data, error, loading, reload } = useFetch(
    (s) => videosApi.list({ page, page_size: PAGE_SIZE, ...(search && { search }), ...(status && { status }) }, s), [page, search, status]);
  const pages = Math.max(1, Math.ceil((data?.count || 0) / PAGE_SIZE));

  const confirmDelete = async () => {
    setBusy(true); setDelError(null);
    try { await videosApi.remove(target.id); setTarget(null); reload(); } catch (e) { setDelError(e.message); setTarget(null); }
    finally { setBusy(false); }
  };
  return (
    <>
      <PageHeader title="Video library" text="Every recording you have uploaded." />
      <div className="mb-4 flex flex-col gap-2 sm:flex-row">
        <div className="flex-1"><SearchBar value={q} onChange={setQ} placeholder="Search by video name" label="Search videos" /></div>
        <select aria-label="Filter by status" className="input sm:w-48" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option><option value="completed">Processed</option><option value="processing">Processing</option><option value="pending">Queued</option><option value="failed">Failed</option>
        </select>
      </div>
      {delError && <div className="mb-4"><ErrorState error={{ message: `Delete failed: ${delError}` }} /></div>}
      {error ? <ErrorState error={error} onRetry={reload} /> : loading ? <LoadingSkeleton rows={3} className="h-40" /> : !data.results.length ? (
        search || status ? <EmptyState icon={Film} title="No videos match" text="Try a different name or clear the status filter." />
          : <EmptyState icon={Film} title="No videos yet" text="Upload CCTV footage to build your library." action={<Link to="/upload" className="btn btn-primary">Upload footage</Link>} />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.results.map((v) => <VideoCard key={v.id} video={v} onDelete={setTarget} />)}</div>
          <nav className="mt-6 flex items-center justify-center gap-3 text-sm" aria-label="Pagination">
            <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={14} /> Previous</button>
            <span className="text-slate-400">Page {page} of {pages}</span>
            <button className="btn" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Next <ChevronRight size={14} /></button>
          </nav>
        </>
      )}
      <ConfirmDialog open={!!target} title="Delete this video?" message={`“${target?.title}” and its analysis will be permanently removed.`} confirmLabel="Delete video" busy={busy} onConfirm={confirmDelete} onCancel={() => setTarget(null)} />
    </>
  );
}
