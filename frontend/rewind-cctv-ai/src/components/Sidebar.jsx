import { NavLink } from 'react-router-dom';
import { Activity, ChevronsLeft, ChevronsRight, History, LayoutDashboard, Library, Rewind, ScanSearch, Settings, Upload, X } from 'lucide-react';

const NAV = [
  ['/', 'Overview', LayoutDashboard], ['/upload', 'Upload Footage', Upload], ['/library', 'Video Library', Library],
  ['/search', 'AI Search', ScanSearch], ['/history', 'Processing History', History], ['/settings', 'Settings', Settings],
];
export default function Sidebar({ collapsed, onToggle, mobileOpen, onClose }) {
  return (
    <>
      {mobileOpen && <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r border-line bg-panel transition-[width,transform] lg:static ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} ${collapsed ? 'w-64 lg:w-[68px]' : 'w-64'}`}>
        <div className="flex h-14 items-center gap-2.5 border-b border-line px-4">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent"><Rewind size={17} className="text-white" aria-hidden /></span>
          {!collapsed && <span className="truncate font-semibold text-slate-100">Rewind CCTV AI</span>}
          <button className="ml-auto lg:hidden" onClick={onClose} aria-label="Close menu"><X size={18} /></button>
        </div>
        <nav className="flex-1 space-y-1 p-2" aria-label="Main">
          {NAV.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={onClose} title={collapsed ? label : undefined}
              className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${isActive ? 'bg-accent-soft text-accent' : 'text-slate-400 hover:bg-raised hover:text-slate-100'}`}>
              <Icon size={18} className="shrink-0" aria-hidden />{!collapsed && label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line p-2">
          <div className="flex items-center gap-3 rounded-lg px-3 py-2">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-raised text-xs font-medium">OP</span>
            {!collapsed && <div className="min-w-0 text-sm"><p className="truncate text-slate-100">Operator</p><p className="truncate text-xs text-slate-500">Signed-in user (auth not configured)</p></div>}
          </div>
          <button onClick={onToggle} className="mt-1 hidden w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-raised lg:flex" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
            {collapsed ? <ChevronsRight size={18} /> : <><ChevronsLeft size={18} /> Collapse</>}
          </button>
        </div>
      </aside>
    </>
  );
}
