import Link from "next/link";
import type { Metadata } from "next";
import { getDeals } from "@/lib/queries/deals";
import { THEMES } from "@/lib/theme-prefixes";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { DealBadge, ConfidencePill } from "@/components/Badges";
import { itemHref } from "@/components/ItemCard";
import { blCatalogUrl, blImageUrl, ils, pct, shortDate } from "@/lib/format";
import type { Rating } from "@/lib/types";

export const metadata: Metadata = { title: "Sniper Deals" };

const RATINGS = ["ALL", "EXCELLENT", "GREAT INVEST", "GOOD"] as const;

export default async function DealsPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | undefined }>;
}) {
  const sp = await searchParams;
  const rating = (RATINGS.includes(sp.rating as (typeof RATINGS)[number]) ? sp.rating : "ALL") as
    | Rating
    | "ALL";
  const minMargin = sp.margin ? Number(sp.margin) : undefined;
  const last24h = sp.window === "24h";
  const prefix = THEMES.find((t) => t.slug === sp.theme && !t.classifier)?.prefix;

  const deals = await getDeals({ rating, minMargin, last24h, prefix, limit: 100 });

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs crumbs={[{ label: "Sniper Deals" }]} />
      <h1 className="mb-1 text-xl font-bold">🎯 Sniper War Room</h1>
      <p className="mb-4 text-[13px] text-ink-muted">
        Underpriced listings vs. fair market value — profit assumes 13% marketplace fees.
      </p>

      <form method="get" className="mb-4 flex flex-wrap items-end gap-2 text-[13px]">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase text-ink-muted">Rating</span>
          <select name="rating" defaultValue={rating} className="rounded border border-edge bg-surface px-2 py-1.5">
            {RATINGS.map((r) => (
              <option key={r} value={r}>{r === "ALL" ? "All ratings" : r}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase text-ink-muted">Min margin %</span>
          <input
            name="margin"
            type="number"
            min={0}
            defaultValue={sp.margin ?? ""}
            placeholder="e.g. 20"
            className="w-24 rounded border border-edge bg-surface px-2 py-1.5"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase text-ink-muted">Window</span>
          <select name="window" defaultValue={sp.window ?? "all"} className="rounded border border-edge bg-surface px-2 py-1.5">
            <option value="all">All time</option>
            <option value="24h">Last 24h (hot)</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase text-ink-muted">Theme</span>
          <select name="theme" defaultValue={sp.theme ?? ""} className="rounded border border-edge bg-surface px-2 py-1.5">
            <option value="">All themes</option>
            {THEMES.filter((t) => !t.classifier).map((t) => (
              <option key={t.slug} value={t.slug}>{t.name}</option>
            ))}
          </select>
        </label>
        <button type="submit" className="rounded bg-yellow px-4 py-1.5 font-semibold text-navy-deep hover:bg-yellow-hover">
          Filter
        </button>
      </form>

      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded border border-edge bg-surface md:block">
        <table className="table-dense w-full">
          <thead>
            <tr>
              <th>Image</th>
              <th>ID</th>
              <th>Name</th>
              <th className="text-right">Market ₪</th>
              <th className="text-right">Profit ₪</th>
              <th className="text-right">Margin</th>
              <th>Rating</th>
              <th>Conf.</th>
              <th>Updated</th>
              <th>Buy</th>
            </tr>
          </thead>
          <tbody>
            {deals.map((item) => (
              <tr key={item.item_id}>
                <td className="w-14">
                  <div className="flex h-10 w-12 items-center justify-center overflow-hidden rounded bg-white">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={blImageUrl(item.item_id)} alt="" loading="lazy" className="max-h-full max-w-full object-contain" />
                  </div>
                </td>
                <td className="font-mono text-[12px]">
                  <Link href={itemHref(item)} className="text-link hover:underline">{item.item_id}</Link>
                </td>
                <td className="max-w-[30ch]">
                  <Link href={itemHref(item)} className="line-clamp-1 hover:text-link">
                    {item.name ?? item.item_id}
                  </Link>
                </td>
                <td className="text-right font-medium">{ils(item.price_new)}</td>
                <td className="text-right font-semibold text-[#16A34A]">{ils(item.cached_profit)}</td>
                <td className="text-right">{pct(item.cached_margin)}</td>
                <td><DealBadge rating={item.cached_rating} /></td>
                <td><ConfidencePill confidence={item.confidence_new} /></td>
                <td className="whitespace-nowrap text-[12px] text-ink-muted">{shortDate(item.updated_at)}</td>
                <td>
                  <a
                    href={blCatalogUrl(item.item_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded bg-yellow px-2 py-0.5 text-[12px] font-semibold text-navy-deep hover:bg-yellow-hover"
                  >
                    Buy ↗
                  </a>
                </td>
              </tr>
            ))}
            {deals.length === 0 && (
              <tr>
                <td colSpan={10} className="py-8 text-center text-ink-muted">
                  No deals match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="grid grid-cols-1 gap-2 md:hidden">
        {deals.map((item) => (
          <div key={item.item_id} className="flex items-center gap-3 rounded border border-edge bg-surface p-3">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded bg-white">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={blImageUrl(item.item_id)} alt="" loading="lazy" className="max-h-full max-w-full object-contain" />
            </div>
            <div className="min-w-0 flex-1">
              <Link href={itemHref(item)} className="block truncate text-[13px] font-medium hover:text-link">
                {item.name ?? item.item_id}
              </Link>
              <p className="font-mono text-[11px] text-ink-muted">{item.item_id}</p>
              <div className="mt-1 flex items-center gap-2">
                <DealBadge rating={item.cached_rating} />
                <span className="text-[12px] font-semibold text-[#16A34A]">
                  +{ils(item.cached_profit)} ({pct(item.cached_margin)})
                </span>
              </div>
            </div>
            <a
              href={blCatalogUrl(item.item_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 rounded bg-yellow px-2.5 py-1 text-[12px] font-semibold text-navy-deep"
            >
              Buy ↗
            </a>
          </div>
        ))}
        {deals.length === 0 && (
          <p className="py-8 text-center text-[13px] text-ink-muted">No deals match these filters.</p>
        )}
      </div>
    </div>
  );
}
