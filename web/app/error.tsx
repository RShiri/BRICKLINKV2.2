"use client"; // Error boundaries must be Client Components

import { useEffect } from "react";
import Link from "next/link";

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-16">
      <div className="mx-auto max-w-lg rounded-lg border border-edge bg-surface p-8 text-center">
        <p className="text-[13px] font-semibold uppercase tracking-wide text-ink-muted">
          Something went wrong
        </p>
        <h1 className="mt-2 text-2xl font-bold text-ink">We hit a snag loading this page</h1>
        <p className="mt-2 text-[13px] text-ink-muted">
          The error was logged{error.digest ? ` (ref ${error.digest})` : ""}. It may be
          temporary — trying again often fixes it.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button
            onClick={() => unstable_retry()}
            className="rounded bg-yellow px-4 py-2 text-[13px] font-semibold text-navy-deep hover:bg-yellow-hover"
          >
            Try again
          </button>
          <Link
            href="/"
            className="rounded border border-edge bg-surface-2 px-4 py-2 text-[13px] font-semibold text-ink hover:border-link hover:text-link"
          >
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
