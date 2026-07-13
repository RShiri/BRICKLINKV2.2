"use client";

import { FormEvent, Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { ScrapeJob } from "@/lib/types";

const STATUS_ICON: Record<ScrapeJob["status"], string> = {
  queued: "⏳",
  running: "🔄",
  done: "✅",
  error: "❌",
};

function AnalyzerForm() {
  const params = useSearchParams();
  const [input, setInput] = useState(params.get("item") ?? "");
  const [deepScan, setDeepScan] = useState(false);
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  function startPolling(ids: number[]) {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/analyze?ids=${ids.join(",")}`);
        if (!res.ok) return;
        const data = await res.json();
        const fetched: ScrapeJob[] = data.jobs ?? [];
        setJobs(fetched);
        if (fetched.every((j) => j.status === "done" || j.status === "error")) {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        /* transient poll failure — keep trying */
      }
    }, 4000);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const items = input
        .split(/[\s,]+/)
        .map((s) => s.trim())
        .filter(Boolean);
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items, deepScan }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Failed to enqueue");
      const enqueued: { id: number; item_id: string }[] = data.jobs ?? [];
      setJobs(
        enqueued.map((j) => ({
          id: j.id,
          item_id: j.item_id,
          item_type: "S",
          deep_scan: deepScan,
          status: "queued",
          error: null,
          created_at: new Date().toISOString(),
          started_at: null,
          finished_at: null,
        })),
      );
      startPolling(enqueued.map((j) => j.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to enqueue jobs");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <h1 className="mb-1 text-xl font-bold">🔎 Set Analyzer</h1>
      <p className="mb-6 text-[13px] text-ink-muted">
        Queue live BrickLink scrapes for sets or minifigs. A worker with a browser picks
        jobs up within seconds; results land on the item pages automatically. Enter up to
        25 IDs separated by spaces or commas (e.g.{" "}
        <code className="rounded bg-surface-2 px-1">76042 10188 sw0001</code>).
      </p>

      <form onSubmit={onSubmit} className="space-y-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={3}
          placeholder="76042, 10188, sw0547…"
          className="w-full rounded border border-edge bg-surface px-3 py-2 font-mono text-[14px]"
        />
        <label className="flex items-center gap-2 text-[13px]">
          <input
            type="checkbox"
            checked={deepScan}
            onChange={(e) => setDeepScan(e.target.checked)}
          />
          Deep scan — also scrape every minifig inside each set (slower)
        </label>
        {error && (
          <p className="rounded bg-[#DC2626]/10 px-3 py-2 text-[13px] text-[#DC2626]">{error}</p>
        )}
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="rounded bg-yellow px-4 py-2 text-[14px] font-semibold text-navy-deep hover:bg-yellow-hover disabled:opacity-50"
        >
          {busy ? "Queueing…" : "🎯 Analyze"}
        </button>
      </form>

      {jobs.length > 0 && (
        <div className="mt-6 overflow-hidden rounded border border-edge bg-surface">
          <table className="table-dense w-full">
            <thead>
              <tr>
                <th>Item</th>
                <th>Status</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td className="font-mono text-[12px]">{job.item_id}</td>
                  <td>
                    {STATUS_ICON[job.status]} {job.status}
                    {job.error && (
                      <span className="block max-w-[40ch] truncate text-[11px] text-[#DC2626]">
                        {job.error}
                      </span>
                    )}
                  </td>
                  <td>
                    {job.status === "done" && (
                      <Link
                        href={
                          /^[a-z]/i.test(job.item_id)
                            ? `/catalog/minifigs/${encodeURIComponent(job.item_id)}`
                            : `/catalog/sets/${encodeURIComponent(job.item_id)}`
                        }
                        className="text-link hover:underline"
                      >
                        View item →
                      </Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function AnalyzerPage() {
  return (
    <Suspense>
      <AnalyzerForm />
    </Suspense>
  );
}
