export default function LoadingSkeleton({ count = 3 }: { count?: number }) {
  const skeletons = Array.from({ length: count });
  return (
    <>
      {skeletons.map((_, i) => (
        <div key={i} className="animate-pulse rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-lg">
          <div className="h-40 bg-slate-800 rounded" />
          <div className="mt-4 space-y-2">
            <div className="h-4 bg-slate-800 rounded w-3/4" />
            <div className="h-4 bg-slate-800 rounded w-1/2" />
          </div>
        </div>
      ))}
    </>
  );
}
