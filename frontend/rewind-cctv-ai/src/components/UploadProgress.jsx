export default function UploadProgress({ percent, name, onCancel }) {
  return (
    <div className="panel p-4" aria-live="polite">
      <div className="mb-2 flex items-center justify-between text-sm"><span className="truncate text-slate-200">{name}</span><span className="font-mono text-slate-400">{percent}%</span></div>
      <div className="h-2 overflow-hidden rounded-full bg-raised" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full bg-accent transition-[width]" style={{ width: `${percent}%` }} />
      </div>
      {percent >= 100 && <p className="mt-2 text-xs text-slate-400">Upload sent. Waiting for the server to confirm…</p>}
      {onCancel && <button className="btn mt-3" onClick={onCancel}>Cancel upload</button>}
    </div>
  );
}
