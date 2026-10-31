import { Search } from 'lucide-react';
export default function SearchBar({ value, onChange, onSubmit, placeholder = 'Search…', busy, label = 'Search', large }) {
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit?.(); }} className="flex gap-2" role="search">
      <div className="relative flex-1">
        <Search size={large ? 20 : 16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" aria-hidden />
        <input aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
          className={`input ${large ? 'py-3.5 pl-10 text-base' : 'pl-9'}`} />
      </div>
      {onSubmit && <button className="btn btn-primary" disabled={busy}>{busy ? 'Searching…' : label}</button>}
    </form>
  );
}
