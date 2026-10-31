import { AlertTriangle, RefreshCw } from 'lucide-react';
export default function ErrorState({ error, onRetry }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-3 rounded-xl border border-bad/30 bg-bad/5 p-5 sm:flex-row sm:items-center">
      <AlertTriangle className="shrink-0 text-bad" size={20} aria-hidden />
      <div className="flex-1 text-sm">
        <p className="font-medium text-slate-100">Something went wrong</p>
        <p className="text-slate-400">{error?.message || 'Unknown error.'}</p>
      </div>
      {onRetry && <button className="btn" onClick={onRetry}><RefreshCw size={14} /> Try again</button>}
    </div>
  );
}
