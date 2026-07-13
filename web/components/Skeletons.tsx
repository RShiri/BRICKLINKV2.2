export function SkeletonCard() {
  return (
    <div className="animate-pulse rounded border border-edge bg-surface p-3">
      <div className="mb-2 h-28 rounded bg-surface-2" />
      <div className="mb-1 h-3 w-16 rounded bg-surface-2" />
      <div className="mb-3 h-4 w-full rounded bg-surface-2" />
      <div className="h-4 w-20 rounded bg-surface-2" />
    </div>
  );
}

export function SkeletonGrid({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 10 }: { rows?: number }) {
  return (
    <div className="animate-pulse overflow-hidden rounded border border-edge bg-surface">
      <div className="h-8 bg-thead" />
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-4 border-t border-edge px-3 py-2">
          <div className="h-10 w-12 rounded bg-surface-2" />
          <div className="h-3 w-16 rounded bg-surface-2" />
          <div className="h-3 flex-1 rounded bg-surface-2" />
          <div className="h-3 w-14 rounded bg-surface-2" />
          <div className="h-3 w-14 rounded bg-surface-2" />
        </div>
      ))}
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="mb-4 h-6 w-64 animate-pulse rounded bg-surface-2" />
      <SkeletonTable />
    </div>
  );
}
