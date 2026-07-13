import Link from "next/link";
import type { Metadata } from "next";
import { getMyCollection, type CollectionEntry } from "@/lib/queries/collections";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { StatTile } from "@/components/StatTile";
import { DealBadge, ConfidencePill } from "@/components/Badges";
import { itemHref } from "@/components/ItemCard";
import { RemoveButton } from "./RemoveButton";
import { signOut } from "./actions";
import { blImageUrl, ils, pct, shortDate } from "@/lib/format";

export const metadata: Metadata = { title: "My Collection" };

const TABS = [
  { key: "hub", label: "💎 Investment Hub" },
  { key: "partout", label: "⚔️ Part-Out Strategist" },
  { key: "all", label: "📦 All Items" },
  { key: "figs", label: "👥 Minifigures" },
] as const;

function filterForTab(entries: CollectionEntry[], tab: string): CollectionEntry[] {
  switch (tab) {
    case "hub":
      return entries
        .filter((e) => ["EXCELLENT", "GREAT INVEST", "GOOD"].includes(e.item.cached_rating ?? ""))
        .sort((a, b) => (b.item.cached_profit ?? 0) - (a.item.cached_profit ?? 0));
    case "partout":
      return entries
        .filter((e) => e.item.item_type === "set")
        .sort((a, b) => (b.item.cached_margin ?? 0) - (a.item.cached_margin ?? 0));
    case "figs":
      return entries.filter((e) => e.item.item_type === "minifig");
    default:
      return entries;
  }
}

export default async function CollectionPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>;
}) {
  const sp = await searchParams;
  const tab = TABS.some((t) => t.key === sp.tab) ? sp.tab! : "hub";
  const entries = await getMyCollection();

  const valueNew = entries.reduce((s, e) => s + (e.item.price_new ?? 0), 0);
  const valueUsed = entries.reduce((s, e) => s + (e.item.price_used ?? 0), 0);
  const profit = entries.reduce((s, e) => s + Math.max(e.item.cached_profit ?? 0, 0), 0);

  const rows = filterForTab(entries, tab);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs crumbs={[{ label: "My Collection" }]} />
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-bold">🔐 My Collection</h1>
        <form action={signOut}>
          <button type="submit" className="rounded border border-edge px-3 py-1 text-[13px] text-ink-muted hover:text-ink">
            Sign out
          </button>
        </form>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Items" value={String(entries.length)} />
        <StatTile label="Value (new)" value={ils(valueNew)} />
        <StatTile label="Value (used)" value={ils(valueUsed)} />
        <StatTile label="Profit potential" value={ils(profit)} />
      </div>

      <div className="mb-4 flex gap-1 overflow-x-auto border-b border-edge">
        {TABS.map((t) => (
          <Link
            key={t.key}
            href={`/collection?tab=${t.key}`}
            className={`whitespace-nowrap border-b-2 px-3 py-1.5 text-[13px] font-medium ${
              tab === t.key
                ? "border-blue text-blue"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </div>

      {tab === "partout" && (
        <p className="mb-3 text-[12px] text-ink-muted">
          Sets ranked by sniper margin — open a set to see its minifig breakdown and
          part-out alert.
        </p>
      )}

      {entries.length === 0 ? (
        <div className="rounded border border-dashed border-edge p-10 text-center text-[13px] text-ink-muted">
          Your collection is empty. Browse the{" "}
          <Link href="/catalog" className="text-link hover:underline">catalog</Link>{" "}
          and use “Add to collection” on any item.
        </div>
      ) : (
        <div className="overflow-x-auto rounded border border-edge bg-surface">
          <table className="table-dense w-full">
            <thead>
              <tr>
                <th>Image</th>
                <th>ID</th>
                <th>Name</th>
                <th className="text-right">New ₪</th>
                <th className="text-right">Used ₪</th>
                <th className="text-right">Profit ₪</th>
                <th className="text-right">Margin</th>
                <th>Rating</th>
                <th>Conf.</th>
                <th>Added</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map(({ item, added_at }) => (
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
                  <td className="max-w-[28ch]">
                    <Link href={itemHref(item)} className="line-clamp-1 hover:text-link">
                      {item.name ?? item.item_id}
                    </Link>
                  </td>
                  <td className="text-right font-medium">
                    {item.price_new && item.price_new > 0 ? ils(item.price_new) : "—"}
                  </td>
                  <td className="text-right">
                    {item.price_used && item.price_used > 0 ? ils(item.price_used) : "—"}
                  </td>
                  <td className="text-right">
                    {item.cached_profit && item.cached_profit > 0 ? ils(item.cached_profit) : "—"}
                  </td>
                  <td className="text-right">
                    {item.cached_margin && item.cached_margin > 0 ? pct(item.cached_margin) : "—"}
                  </td>
                  <td><DealBadge rating={item.cached_rating} /></td>
                  <td><ConfidencePill confidence={item.confidence_new} /></td>
                  <td className="whitespace-nowrap text-[12px] text-ink-muted">{shortDate(added_at)}</td>
                  <td><RemoveButton itemId={item.item_id} /></td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-ink-muted">
                    Nothing in this view.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
