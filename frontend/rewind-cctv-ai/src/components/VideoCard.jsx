import { Link } from 'react-router-dom';
import { Film, Trash2 } from 'lucide-react';
import ProcessingBadge from './ProcessingBadge.jsx';
import { formatBytes, formatDate, formatDuration } from '../utils/format.js';
export default function VideoCard({ video, onDelete }) {
  return (
    <div className="panel overflow-hidden">
      <div className="grid aspect-video place-items-center bg-ink">
        {video.thumbnail ? <img src={video.thumbnail} alt="" className="h-full w-full object-cover" /> : <Film className="text-slate-600" size={32} aria-hidden />}
      </div>
      <div className="space-y-2 p-4">
        <div className="flex items-start justify-between gap-2"><h3 className="truncate font-medium text-slate-100" title={video.title}>{video.title}</h3><ProcessingBadge status={video.status} /></div>
        <p className="text-xs text-slate-400">{formatDate(video.uploadedAt)} · {formatDuration(video.duration)} · {formatBytes(video.size)}</p>
        <div className="flex gap-2 pt-1">
          <Link to={`/library/${video.id}`} className="btn flex-1">View details</Link>
          <button className="btn btn-danger" aria-label={`Delete ${video.title}`} onClick={() => onDelete(video)}><Trash2 size={15} /></button>
        </div>
      </div>
    </div>
  );
}
