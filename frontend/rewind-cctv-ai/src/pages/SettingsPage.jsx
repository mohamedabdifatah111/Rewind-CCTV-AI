import { RefreshCw } from 'lucide-react';
import PageHeader from './PageHeader.jsx';
import ErrorState from '../components/ErrorState.jsx';
import { API_BASE_URL, systemApi } from '../services/api.js';
import { useFetch } from '../hooks/useApi.js';

const Row = ({ k, v }) => <div className="flex justify-between gap-4 border-t border-line py-2.5 text-sm first:border-0"><dt className="text-slate-400">{k}</dt><dd className="text-right text-slate-100">{v ?? 'Not provided by backend'}</dd></div>;

export default function SettingsPage() {
  const health = useFetch(() => systemApi.health(), []);
  const cfg = useFetch(() => systemApi.config(), []);
  const c = cfg.data;
  const refresh = () => { health.reload(); cfg.reload(); };
  return (
    <>
      <PageHeader title="Settings"><button className="btn" onClick={refresh}><RefreshCw size={14} /> Re-check connection</button></PageHeader>
      <div className="grid max-w-3xl gap-4">
        <section className="panel p-4">
          <h2 className="mb-2 font-medium text-slate-100">API connection</h2>
          <dl>
            <Row k="Backend URL" v={<span className="font-mono">{API_BASE_URL}</span>} />
            <Row k="Status" v={health.loading ? 'Checking…' : health.error ? <span className="text-bad">Unreachable</span> : <span className="text-ok">Connected</span>} />
          </dl>
          {health.error && <div className="mt-3"><ErrorState error={health.error} /></div>}
        </section>
        <section className="panel p-4">
          <h2 className="mb-2 font-medium text-slate-100">Application</h2>
          <dl>
            <Row k="Application" v="Rewind CCTV AI" />
            <Row k="Backend version" v={c?.version} />
            <Row k="Analysis model" v={c?.model} />
            <Row k="Supported formats" v={c?.formats?.length ? c.formats.join(', ').toUpperCase() : null} />
            <Row k="Maximum upload size" v={c?.maxMb ? `${c.maxMb} MB` : null} />
          </dl>
          {cfg.error && <p className="mt-3 text-sm text-warn">Config endpoint unavailable: {cfg.error.message}</p>}
        </section>
        <section className="panel p-4">
          <h2 className="mb-2 font-medium text-slate-100">Privacy and retention</h2>
          <p className="text-sm text-slate-400">Footage and extracted frames are stored and analysed by your backend. Sampled frames are sent to the Gemma 4 analysis service you configured there. This app stores nothing in the browser and holds no API keys; all secrets stay on the server.</p>
          <p className="mt-2 text-sm text-slate-400">Retention: {c?.retentionDays ? `${c.retentionDays} days` : 'not reported by the backend. Check your server policy.'} Deleting a video from the library asks the backend to remove it.</p>
        </section>
      </div>
    </>
  );
}
