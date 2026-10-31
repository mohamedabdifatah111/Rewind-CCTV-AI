export default function EmptyState({ icon: Icon, title, text, action }) {
  return (
    <div className="panel flex flex-col items-center px-6 py-14 text-center">
      {Icon && <Icon size={28} className="mb-3 text-slate-500" aria-hidden />}
      <h3 className="font-medium text-slate-100">{title}</h3>
      {text && <p className="mt-1 max-w-md text-sm text-slate-400">{text}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
