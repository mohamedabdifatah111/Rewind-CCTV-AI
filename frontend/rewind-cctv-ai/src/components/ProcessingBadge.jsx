import { CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react';
const MAP = {
  completed: ['Processed', 'text-ok bg-ok/10 border-ok/30', CheckCircle2],
  processing: ['Processing', 'text-accent bg-accent-soft border-accent/30', Loader2],
  pending: ['Queued', 'text-slate-300 bg-raised border-line', Clock],
  failed: ['Failed', 'text-bad bg-bad/10 border-bad/30', XCircle],
};
export default function ProcessingBadge({ status }) {
  const key = ['complete', 'done', 'processed', 'success'].includes(status) ? 'completed' : ['queued', 'uploaded'].includes(status) ? 'pending' : status;
  const [label, cls, Icon] = MAP[key] || [status || 'Unknown', MAP.pending[1], Clock];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      <Icon size={12} className={key === 'processing' ? 'animate-spin' : ''} aria-hidden /> {label}
    </span>
  );
}
