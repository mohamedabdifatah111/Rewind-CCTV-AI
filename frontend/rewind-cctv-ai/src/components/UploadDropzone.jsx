import { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';
export default function UploadDropzone({ onFile, disabled, accept, hint }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const pick = (files) => files?.[0] && onFile(files[0]);
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); !disabled && setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); !disabled && pick(e.dataTransfer.files); }}
      className={`flex flex-col items-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors ${over ? 'border-accent bg-accent-soft' : 'border-line bg-panel'} ${disabled ? 'opacity-50' : ''}`}
    >
      <UploadCloud size={32} className="mb-3 text-accent" aria-hidden />
      <p className="font-medium text-slate-100">Drop a CCTV recording here</p>
      <p className="mt-1 text-sm text-slate-400">{hint}</p>
      <button type="button" className="btn mt-4" disabled={disabled} onClick={() => input.current.click()}>Choose file</button>
      <input ref={input} type="file" accept={accept} hidden onChange={(e) => { pick(e.target.files); e.target.value = ''; }} aria-label="Choose video file" />
    </div>
  );
}
