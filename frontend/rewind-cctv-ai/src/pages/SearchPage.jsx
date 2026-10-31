import { useRef, useState } from 'react';
import { Info, ScanSearch } from 'lucide-react';
import PageHeader from './PageHeader.jsx';
import SearchBar from '../components/SearchBar.jsx';
import TimestampResult from '../components/TimestampResult.jsx';
import VideoPlayer from '../components/VideoPlayer.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import { searchApi, videosApi } from '../services/api.js';
import { useFetch } from '../hooks/useApi.js';

const EXAMPLES = ['Show me when someone entered the room', 'Find the moment someone was carrying a bag', 'When did someone leave the building?', 'Find moments when a person approached the desk', 'Show me when someone placed an object on the table'];

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [videoId, setVideoId] = useState('');
  const [state, setState] = useState({ status: 'idle', results: [], error: null, asked: '' });
  const [validation, setValidation] = useState('');
  const [active, setActive] = useState(null); // { idx, url, time, nonce }
  const [openError, setOpenError] = useState(null);
  const cache = useRef({});
  const { data: vids } = useFetch((s) => videosApi.list({ status: 'completed', page_size: 100 }, s), []);

  const run = async (text = query) => {
    const q = text.trim();
    if (q.length < 3) { setValidation('Describe what you are looking for (at least 3 characters).'); return; }
    setValidation(''); setActive(null); setOpenError(null);
    setState({ status: 'loading', results: [], error: null, asked: q });
    try { setState({ status: 'done', results: await searchApi.query(q, videoId || null), error: null, asked: q }); }
    catch (e) { setState({ status: 'error', results: [], error: e, asked: q }); }
  };
  const open = async (r, idx) => {
    setOpenError(null);
    try {
      cache.current[r.videoId] ||= (await videosApi.get(r.videoId)).url;
      setActive({ idx, url: cache.current[r.videoId], time: r.time, nonce: Date.now() });
    } catch (e) { setOpenError(e.message); }
  };
  const processed = vids?.results || [];

  return (
    <>
      <PageHeader title="AI search" text="Describe a moment in plain language and jump straight to it." />
      <div className="space-y-3">
        <SearchBar large value={query} onChange={setQuery} onSubmit={() => run()} busy={state.status === 'loading'} placeholder="e.g. Show me when someone entered the room" label="Search footage" />
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <label htmlFor="scope" className="text-sm text-slate-400">Search in</label>
          <select id="scope" className="input sm:w-72" value={videoId} onChange={(e) => setVideoId(e.target.value)}>
            <option value="">All processed videos</option>{processed.map((v) => <option key={v.id} value={v.id}>{v.title}</option>)}
          </select>
        </div>
        {validation && <p role="alert" className="text-sm text-bad">{validation}</p>}
        <p className="flex items-start gap-2 text-xs text-slate-500"><Info size={14} className="mt-0.5 shrink-0" />The AI searches sampled frames, not every frame, and can miss events that happen between samples. Check the footage before relying on a result.</p>
        <div className="flex flex-wrap gap-2">{EXAMPLES.map((e) => <button key={e} className="rounded-full border border-line px-3 py-1 text-xs text-slate-400 hover:bg-raised hover:text-slate-100" onClick={() => { setQuery(e); run(e); }}>{e}</button>)}</div>
      </div>
      <div className="mt-6">
        {state.status === 'error' && <ErrorState error={state.error} onRetry={() => run(state.asked)} />}
        {state.status === 'loading' && <p className="text-sm text-slate-400" role="status">Searching sampled frames…</p>}
        {state.status === 'idle' && <EmptyState icon={ScanSearch} title="Ask about your footage" text="Matches show the video, the timestamp and what the AI saw." />}
        {state.status === 'done' && !state.results.length && <EmptyState icon={ScanSearch} title="No matching moments" text={`Nothing matched “${state.asked}”. The AI only sees sampled frames, so try different wording, a broader description, or another video.`} />}
        {state.status === 'done' && state.results.length > 0 && (
          <div className="grid gap-6 lg:grid-cols-[1fr_420px]">
            <div className="space-y-2" aria-live="polite">
              <p className="text-sm text-slate-400">{state.results.length} matching moment{state.results.length > 1 ? 's' : ''}</p>
              {state.results.map((r, i) => <TimestampResult key={i} title={r.title} time={r.time} description={r.description} active={active?.idx === i} onOpen={() => open(r, i)} />)}
            </div>
            <div className="lg:sticky lg:top-0 lg:self-start">
              {openError && <ErrorState error={{ message: openError }} />}
              {active ? <VideoPlayer src={active.url} seek={{ time: active.time, nonce: active.nonce }} /> : <div className="panel grid aspect-video place-items-center p-4 text-center text-sm text-slate-500">Select a result to play it here.</div>}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
