import Link from "next/link";
import type { Metadata } from "next";
import {
  getCatalogSet,
  getItem,
  getSetMinifigs,
  getThemePath,
} from "@/lib/queries/catalog";
import { getPriceHistory } from "@/lib/queries/prices";
import { Breadcrumbs, type Crumb } from "@/components/Breadcrumbs";
import { PriceGuideTable } from "@/components/PriceGuideTable";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { DealBadge, ConfidencePill, LifecycleBadge } from "@/components/Badges";
import { CollectionButton } from "@/components/CollectionButton";
import { isInMyCollection } from "@/lib/queries/collections";
import { blCatalogUrl, blImageUrl, ils, num, pct, shortDate } from "@/lib/format";

type Params = { setNum: string };

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { setNum } = await params;
  return { title: `Set ${decodeURIComponent(setNum)}` };
}

export default async function SetPage({ params }: { params: Promise<Params> }) {
  const { setNum: raw } = await params;
  const setNum = decodeURIComponent(raw);
  const blId = setNum.replace(/-1$/, "");

  const [item, catalogSet, minifigs, history, inCollection] = await Promise.all([
    getItem(blId).then((i) => i ?? getItem(setNum)),
    getCatalogSet(setNum),
    getSetMinifigs(setNum),
    getPriceHistory(blId, 90),
    isInMyCollection(blId),
  ]);

  const themePath = await getThemePath(catalogSet?.theme_id ?? null);
  const name = item?.name ?? catalogSet?.name ?? setNum;

  const crumbs: Crumb[] = [{ label: "Catalog", href: "/catalog" }];
  for (const t of themePath) crumbs.push({ label: t.name });
  crumbs.push({ label: setNum });

  const figsTotalNew = minifigs.reduce(
    (s, f) => s + (f.item?.price_new ?? 0) * f.quantity,
    0,
  );
  const figsPctOfSet =
    item?.price_used && item.price_used > 0 && figsTotalNew > 0
      ? (figsTotalNew / item.price_used) * 100
      : null;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs crumbs={crumbs} />

      <div className="flex flex-col gap-6 lg:flex-row">
        {/* Image + specs */}
        <div className="w-full shrink-0 lg:w-72">
          <div className="flex h-56 items-center justify-center rounded border border-edge bg-white p-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={catalogSet?.img_url ?? blImageUrl(blId)}
              alt={name}
              className="max-h-full max-w-full object-contain"
            />
          </div>
          <dl className="mt-3 space-y-1 rounded border border-edge bg-surface p-3 text-[13px]">
            <div className="flex justify-between">
              <dt className="text-ink-muted">Set number</dt>
              <dd className="font-mono">{setNum}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Year</dt>
              <dd>{item?.year_released ?? catalogSet?.year ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Parts</dt>
              <dd>{num(catalogSet?.num_parts ?? null)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Minifigs</dt>
              <dd>{minifigs.length ? num(minifigs.reduce((s, f) => s + f.quantity, 0)) : "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Last scraped</dt>
              <dd>{shortDate(item?.updated_at)}</dd>
            </div>
          </dl>
          <a
            href={blCatalogUrl(blId)}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 block rounded border border-edge px-3 py-1.5 text-center text-[13px] text-link hover:bg-surface-2"
          >
            View on BrickLink ↗
          </a>
        </div>

        {/* Main column */}
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-bold">{name}</h1>
            <LifecycleBadge lifecycle={item?.lifecycle} />
            <DealBadge rating={item?.cached_rating} />
            <CollectionButton itemId={blId} initialInCollection={inCollection} />
          </div>

          {item ? (
            <>
              {/* Market summary */}
              <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded border border-edge bg-surface p-3">
                  <p className="text-[11px] uppercase text-ink-muted">Market (new)</p>
                  <p className="text-lg font-bold">{ils(item.price_new)}</p>
                  <ConfidencePill confidence={item.confidence_new} />
                </div>
                <div className="rounded border border-edge bg-surface p-3">
                  <p className="text-[11px] uppercase text-ink-muted">Market (used)</p>
                  <p className="text-lg font-bold">{ils(item.price_used)}</p>
                  <ConfidencePill confidence={item.confidence_used} />
                </div>
                <div className="rounded border border-edge bg-surface p-3">
                  <p className="text-[11px] uppercase text-ink-muted">Buy target</p>
                  <p className="text-lg font-bold text-[#16A34A]">{ils(item.buy_target)}</p>
                  <p className="text-[11px] text-ink-muted">80% of market</p>
                </div>
                <div className="rounded border border-edge bg-surface p-3">
                  <p className="text-[11px] uppercase text-ink-muted">Sniper margin</p>
                  <p className="text-lg font-bold">
                    {item.cached_margin && item.cached_margin > 0 ? pct(item.cached_margin) : "—"}
                  </p>
                  <p className="text-[11px] text-ink-muted">
                    profit {item.cached_profit && item.cached_profit > 0 ? ils(item.cached_profit) : "—"}
                  </p>
                </div>
              </div>

              {/* Price guide quadrant */}
              {item.guide && (
                <section className="mb-6">
                  <h2 className="mb-2 text-base font-bold">Price Guide</h2>
                  <PriceGuideTable guide={item.guide} />
                  <p className="mt-1 text-[11px] text-ink-muted">
                    Filtered listings only (incomplete sets, bulk lots, and statistical
                    outliers removed). All prices in ₪.{" "}
                    <Link href="/price-guide" className="text-link hover:underline">
                      Methodology
                    </Link>
                  </p>
                </section>
              )}

              {/* History */}
              <section className="mb-6">
                <h2 className="mb-2 text-base font-bold">Price history (90 days)</h2>
                <PriceHistoryChart history={history} />
              </section>
            </>
          ) : (
            <div className="mb-6 rounded border border-dashed border-edge p-6 text-center text-[13px] text-ink-muted">
              No price data yet for this set.{" "}
              <Link href={`/tools/analyzer?item=${blId}`} className="text-link hover:underline">
                Run the analyzer
              </Link>{" "}
              to scrape live BrickLink prices.
            </div>
          )}

          {/* Minifig breakdown */}
          {minifigs.length > 0 && (
            <section>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <h2 className="text-base font-bold">Minifigure breakdown</h2>
                {figsPctOfSet != null && (
                  <span
                    className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${
                      figsPctOfSet >= 80
                        ? "bg-[#16A34A]/10 text-[#16A34A]"
                        : "bg-surface-2 text-ink-muted"
                    }`}
                  >
                    figs = {pct(figsPctOfSet)} of used set price
                    {figsPctOfSet >= 80 ? " · PART-OUT CANDIDATE" : ""}
                  </span>
                )}
              </div>
              <div className="overflow-x-auto rounded border border-edge bg-surface">
                <table className="table-dense w-full">
                  <thead>
                    <tr>
                      <th>Image</th>
                      <th>ID</th>
                      <th>Name</th>
                      <th className="text-right">Qty</th>
                      <th className="text-right">New ₪</th>
                      <th className="text-right">Used ₪</th>
                    </tr>
                  </thead>
                  <tbody>
                    {minifigs.map((fig) => (
                      <tr key={fig.fig_num}>
                        <td className="w-14">
                          <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded bg-white">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={fig.bl_id ? blImageUrl(fig.bl_id) : (fig.img_url ?? "")}
                              alt=""
                              loading="lazy"
                              className="max-h-full max-w-full object-contain"
                            />
                          </div>
                        </td>
                        <td className="font-mono text-[12px]">
                          {fig.bl_id ? (
                            <Link
                              href={`/catalog/minifigs/${encodeURIComponent(fig.bl_id)}`}
                              className="text-link hover:underline"
                            >
                              {fig.bl_id}
                            </Link>
                          ) : (
                            fig.fig_num
                          )}
                        </td>
                        <td>{fig.name}</td>
                        <td className="text-right">{fig.quantity}</td>
                        <td className="text-right font-medium">
                          {fig.item?.price_new ? ils(fig.item.price_new) : "—"}
                        </td>
                        <td className="text-right">
                          {fig.item?.price_used ? ils(fig.item.price_used) : "—"}
                        </td>
                      </tr>
                    ))}
                    <tr className="font-semibold">
                      <td colSpan={4}>Total minifig value (new)</td>
                      <td className="text-right">{ils(figsTotalNew)}</td>
                      <td />
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
