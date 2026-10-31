export default function LoadingSkeleton({ rows = 4, className = 'h-12' }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => <div key={i} className={`animate-pulse rounded-lg bg-raised ${className}`} />)}
    </div>
  );
}
