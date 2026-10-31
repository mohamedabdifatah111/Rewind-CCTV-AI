export default function PageHeader({ title, text, children }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div><h1 className="text-xl font-semibold text-slate-100">{title}</h1>{text && <p className="mt-1 text-sm text-slate-400">{text}</p>}</div>
      {children}
    </div>
  );
}
