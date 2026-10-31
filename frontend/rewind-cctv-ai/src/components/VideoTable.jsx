import { Link } from 'react-router-dom';
import ProcessingBadge from './ProcessingBadge.jsx';
import { formatDate, formatDuration } from '../utils/format.js';
export default function VideoTable({ videos }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="text-slate-400"><tr><th className="py-2 pr-4 font-medium">Video</th><th className="pr-4 font-medium">Uploaded</th><th className="pr-4 font-medium">Status</th><th className="pr-4 font-medium">Duration</th><th className="font-medium"><span className="sr-only">Action</span></th></tr></thead>
        <tbody>
          {videos.map((v) => (
            <tr key={v.id} className="border-t border-line">
              <td className="max-w-[240px] truncate py-3 pr-4 text-slate-100">{v.title}</td>
              <td className="pr-4 text-slate-400">{formatDate(v.uploadedAt)}</td>
              <td className="pr-4"><ProcessingBadge status={v.status} /></td>
              <td className="pr-4 font-mono text-slate-400">{formatDuration(v.duration)}</td>
              <td className="text-right"><Link className="btn" to={`/library/${v.id}`}>Open</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
