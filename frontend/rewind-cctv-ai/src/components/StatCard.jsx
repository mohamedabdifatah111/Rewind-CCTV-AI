export default function StatCard({ label, value, icon: Icon, tone = 'text-slate-100' }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between text-sm text-slate-400">{label}{Icon && <Icon size={16} aria-hidden />}</div>
      <div className={`mt-2 text-3xl font-semibold tabular-nums ${tone}`}>{value ?? '—'}</div>
    </div>
  );
}
