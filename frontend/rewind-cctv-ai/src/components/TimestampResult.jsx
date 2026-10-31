import { Play } from 'lucide-react';
import { formatTimestamp } from '../utils/format.js';
export default function TimestampResult({ time, description, title, onOpen, active }) {
  return (
    <button onClick={onOpen} className={`flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-colors hover:bg-raised ${active ? 'border-accent bg-accent-soft' : 'border-line bg-panel'}`}>
      <span className="flex shrink-0 items-center gap-1.5 rounded-md bg-accent px-2 py-1 font-mono text-xs text-white"><Play size={11} aria-hidden /> {formatTimestamp(time)}</span>
      <span className="min-w-0 text-sm">
        {title && <span className="block truncate font-medium text-slate-100">{title}</span>}
        <span className="text-slate-400">{description}</span>
      </span>
    </button>
  );
}
