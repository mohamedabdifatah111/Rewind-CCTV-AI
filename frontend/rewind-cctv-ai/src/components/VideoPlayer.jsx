import { useEffect, useRef } from 'react';
import { VideoOff } from 'lucide-react';

/** HTML5 player on the original file. `seek` = { time (seconds), nonce } — a new nonce seeks and plays. */
export default function VideoPlayer({ src, seek }) {
  const ref = useRef(null);
  useEffect(() => {
    const v = ref.current;
    if (!v || !seek || !Number.isFinite(seek.time)) return undefined;
    const go = () => { v.currentTime = seek.time; v.play().catch(() => {}); };
    if (v.readyState >= 1) { go(); return undefined; }
    v.addEventListener('loadedmetadata', go, { once: true });
    return () => v.removeEventListener('loadedmetadata', go);
  }, [seek, src]);
  if (!src) return (
    <div className="panel grid aspect-video place-items-center text-sm text-slate-400"><span className="flex items-center gap-2"><VideoOff size={18} /> No playable file URL from the backend.</span></div>
  );
  return <video ref={ref} src={src} controls preload="metadata" className="aspect-video w-full rounded-xl border border-line bg-black" />;
}
