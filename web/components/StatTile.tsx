export function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded border border-edge bg-surface p-4">
      <p className="text-[12px] font-medium uppercase tracking-wide text-ink-muted">{label}</p>
      <p className="mt-1 text-xl font-bold text-ink">{value}</p>
      {hint && <p className="mt-0.5 text-[12px] text-ink-muted">{hint}</p>}
    </div>
  );
}
