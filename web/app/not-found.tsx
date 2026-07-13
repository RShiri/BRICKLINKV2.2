import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Page not found",
};

export default function NotFound() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16">
      <div className="mx-auto max-w-lg rounded-lg border border-edge bg-surface p-8 text-center">
        <p className="text-[13px] font-semibold uppercase tracking-wide text-ink-muted">
          404 — Not found
        </p>
        <h1 className="mt-2 text-2xl font-bold text-ink">
          This brick isn&apos;t in the catalog
        </h1>
        <p className="mt-2 text-[13px] text-ink-muted">
          The page you&apos;re looking for doesn&apos;t exist, or the item id has no data yet.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            href="/"
            className="rounded bg-yellow px-4 py-2 text-[13px] font-semibold text-navy-deep hover:bg-yellow-hover"
          >
            Back to home
          </Link>
          <Link
            href="/catalog"
            className="rounded border border-edge bg-surface-2 px-4 py-2 text-[13px] font-semibold text-ink hover:border-link hover:text-link"
          >
            Browse catalog
          </Link>
        </div>
      </div>
    </div>
  );
}
