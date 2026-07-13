import Link from "next/link";
import type { Metadata } from "next";
import {
  blIdFor,
  getCatalogMinifig,
  getFigAppearsIn,
  getInventoryParts,
  getItem,
  rbIdFor,
} from "@/lib/queries/catalog";
import { PartsTable } from "@/components/PartsTable";
import { getPriceHistory } from "@/lib/queries/prices";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { PriceGuideTable } from "@/components/PriceGuideTable";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { DealBadge, ConfidencePill, LifecycleBadge } from "@/components/Badges";
import { CollectionButton } from "@/components/CollectionButton";
import { ItemImage } from "@/components/ItemImage";
import { isInMyCollection } from "@/lib/queries/collections";
import { blCatalogUrl, blImageUrl, ils, pct, shortDate } from "@/lib/format";

type Params = { id: string };

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { id } = await params;
  return { title: `Minifig ${decodeURIComponent(id)}` };
}

export default async function MinifigPage({ params }: { params: Promise<Params> }) {
  const { id: raw } = await params;
  const id = decodeURIComponent(raw);

  // Canonical id is the BrickLink one (prices key on it); accept fig-* too.
  const isRbId = id.startsWith("fig-");
  const blId = isRbId ? await blIdFor("minifig", id) : id;
  const rbId = isRbId ? id : await rbIdFor("minifig", id);

  const [item, catalogFig, history, appearsIn, inCollection, parts] = await Promise.all([
    blId ? getItem(blId) : Promise.resolve(null),
    rbId ? getCatalogMinifig(rbId) : Promise.resolve(null),
    blId ? getPriceHistory(blId, 90) : Promise.resolve([]),
    rbId ? getFigAppearsIn(rbId) : Promise.resolve([]),
    blId ? isInMyCollection(blId) : Promise.resolve(null),
    rbId ? getInventoryParts(rbId) : Promise.resolve([]),
  ]);

  const name = item?.name ?? catalogFig?.name ?? id;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs
        crumbs={[{ label: "Catalog", href: "/catalog" }, { label: "Minifigs" }, { label: blId ?? id }]}
      />

      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="w-full shrink-0 lg:w-64">
          <div className="flex h-56 items-center justify-center rounded border border-edge bg-white p-2">
            <ItemImage
              src={blId ? blImageUrl(blId) : catalogFig?.img_url}
              alt={name}
              className="max-h-full max-w-full object-contain"
            />
          </div>
          <dl className="mt-3 space-y-1 rounded border border-edge bg-surface p-3 text-[13px]">
            <div className="flex justify-between">
              <dt className="text-ink-muted">BrickLink ID</dt>
              <dd className="font-mono">{blId ?? "unmapped"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Rebrickable ID</dt>
              <dd className="font-mono">{rbId ?? "unmapped"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Year</dt>
              <dd>{item?.year_released ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Last scraped</dt>
              <dd>{shortDate(item?.updated_at)}</dd>
            </div>
          </dl>
          {blId && (
            <a
              href={blCatalogUrl(blId)}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 block rounded border border-edge px-3 py-1.5 text-center text-[13px] text-link hover:bg-surface-2"
            >
              View on BrickLink ↗
            </a>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-bold">{name}</h1>
            <LifecycleBadge lifecycle={item?.lifecycle} />
            <DealBadge rating={item?.cached_rating} />
            {blId && <CollectionButton itemId={blId} initialInCollection={inCollection} />}
          </div>

          {item ? (
            <>
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

              {item.guide && (
                <section className="mb-6">
                  <h2 className="mb-2 text-base font-bold">Price Guide</h2>
                  <PriceGuideTable guide={item.guide} />
                </section>
              )}

              <section className="mb-6">
                <h2 className="mb-2 text-base font-bold">Price history (90 days)</h2>
                <PriceHistoryChart history={history} />
              </section>
            </>
          ) : (
            <div className="mb-6 rounded border border-dashed border-edge p-6 text-center text-[13px] text-ink-muted">
              No price data yet for this minifigure.
            </div>
          )}

          {appearsIn.length > 0 && (
            <section>
              <h2 className="mb-2 text-base font-bold">Appears in sets</h2>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {appearsIn.map((set) => (
                  <li key={set.set_num}>
                    <Link
                      href={`/catalog/sets/${encodeURIComponent(set.set_num)}`}
                      className="flex items-center gap-2 rounded border border-edge bg-surface px-3 py-2 text-[13px] hover:border-link"
                    >
                      <span className="font-mono text-ink-muted">{set.set_num}</span>
                      <span className="min-w-0 flex-1 truncate">{set.name}</span>
                      <span className="text-ink-muted">{set.year ?? ""}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Part inventory */}
          {parts.length > 0 && (
            <section className="mt-6">
              <h2 className="mb-2 text-base font-bold">
                Parts ({parts.filter((p) => !p.is_spare).reduce((s, p) => s + p.quantity, 0)})
              </h2>
              <PartsTable parts={parts} />
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
