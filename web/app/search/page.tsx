import Link from "next/link";
import type { Metadata } from "next";
import { searchCatalog, type SearchScope } from "@/lib/queries/search";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { DealBadge } from "@/components/Badges";
import { blImageUrl, ils } from "@/lib/format";
import type { SearchResult } from "@/lib/types";

export const metadata: Metadata = { title: "Search" };

const TABS: { value: SearchScope; label: string }[] = [
  { value: "all", label: "All" },
  { value: "sets", label: "Sets" },
  { value: "minifigs", label: "Minifigs" },
  { value: "parts", label: "Parts" },
];

function resultHref(r: SearchResult): string {
  if (r.result_type === "set") return `/catalog/sets/${encodeURIComponent(r.id)}`;
  if (r.result_type === "minifig") return `/catalog/minifigs/${encodeURIComponent(r.id)}`;
  return `/catalog/parts/${encodeURIComponent(r.id)}`;
}

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; scope?: string }>;
}) {
  const sp = await searchParams;
  const q = sp.q ?? "";
  const scope = (TABS.some((t) => t.value === sp.scope) ? sp.scope : "all") as SearchScope;
  const results = q ? await searchCatalog(q, scope, 50) : [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs crumbs={[{ label: "Search" }]} />
      <h1 className="mb-4 text-xl font-bold">
        {q ? `Results for “${q}”` : "Search"}
      </h1>

      <div className="mb-4 flex gap-1 border-b border-edge">
        {TABS.map((tab) => (
          <Link
            key={tab.value}
            href={`/search?q=${encodeURIComponent(q)}&scope=${tab.value}`}
            className={`border-b-2 px-3 py-1.5 text-[13px] font-medium ${
              scope === tab.value
                ? "border-blue text-blue"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      {q === "" ? (
        <p className="text-[13px] text-ink-muted">
          Type a set number, minifig ID, or name in the search bar above.
        </p>
      ) : results.length === 0 ? (
        <p className="text-[13px] text-ink-muted">No results found.</p>
      ) : (
        <ul className="divide-y divide-edge overflow-hidden rounded border border-edge bg-surface">
          {results.map((r) => (
            <li key={`${r.result_type}-${r.id}`}>
              <Link
                href={resultHref(r)}
                className="flex items-center gap-3 px-3 py-2 text-[13px] hover:bg-surface-2"
              >
                <span className="flex h-10 w-12 shrink-0 items-center justify-center overflow-hidden rounded bg-white">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={
                      r.result_type === "part"
                        ? (r.img_url ?? "")
                        : (r.img_url ?? blImageUrl(r.id))
                    }
                    alt=""
                    loading="lazy"
                    className="max-h-full max-w-full object-contain"
                  />
                </span>
                <span className="w-20 shrink-0 font-mono text-[12px] text-ink-muted">{r.id}</span>
                <span className="min-w-0 flex-1 truncate">{r.name}</span>
                <span className="shrink-0 rounded bg-surface-2 px-1.5 py-0.5 text-[11px] uppercase text-ink-muted">
                  {r.result_type}
                </span>
                <DealBadge rating={r.rating} />
                {r.price_new != null && r.price_new > 0 && (
                  <span className="w-20 shrink-0 text-right font-medium">{ils(r.price_new)}</span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
