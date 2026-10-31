import { Link } from 'react-router-dom';
import { Bell, Loader2, Menu } from 'lucide-react';
import { dashboardApi } from '../services/api.js';
import { useFetch, usePolling } from '../hooks/useApi.js';

export default function Topbar({ onMenu }) {
  const { data, error, reload } = useFetch((s) => dashboardApi.stats(s), []);
  usePolling(reload, 10000, true);
  const n = data?.processing ?? 0;
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-panel px-4">
      <button className="btn px-2 lg:hidden" onClick={onMenu} aria-label="Open menu"><Menu size={18} /></button>
      <span className="flex items-center gap-2 text-sm">
        <span className={`h-2 w-2 rounded-full ${error ? 'bg-bad' : data ? 'bg-ok' : 'bg-slate-600'}`} />
        <span className="text-slate-400">{error ? 'Backend unreachable' : data ? 'Backend connected' : 'Connecting…'}</span>
      </span>
      <Link to="/history" className="btn ml-auto" aria-label={`${n} videos processing`}>
        {n > 0 ? <Loader2 size={15} className="animate-spin text-accent" /> : <Bell size={15} />}
        <span className="hidden sm:inline">{n > 0 ? `${n} processing` : 'Nothing processing'}</span>
        {data?.failed > 0 && <span className="rounded-full bg-bad px-1.5 text-xs text-white">{data.failed}</span>}
      </Link>
    </header>
  );
}
