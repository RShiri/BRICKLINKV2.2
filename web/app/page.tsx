import Link from "next/link";
import { getHomeStats, getRecentlyUpdated } from "@/lib/queries/catalog";
import { getTopDeals } from "@/lib/queries/deals";
import { THEMES } from "@/lib/theme-prefixes";
import { StatTile } from "@/components/StatTile";
import { ItemCard } from "@/components/ItemCard";
import { ils, num, shortDate } from "@/lib/format";

// Stats and deals must be live, not frozen at build time.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [stats, topDeals, recent] = await Promise.all([
    getHomeStats(),
    getTopDeals(6),
    getRecentlyUpdated(6),
  ]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      {/* Hero */}
      <section className="mb-8 rounded-lg bg-navy px-6 py-8 text-white">
        <h1 className="text-2xl font-bold sm:text-3xl">
          LEGO® market intelligence, <span className="text-yellow">sniper precision</span>
        </h1>
        <p className="mt-2 max-w-2xl text-white/80">
          Live BrickLink market prices with statistical filtering, fair-value estimates,
          and profit-rated deals across sets and minifigures.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            href="/deals"
            className="rounded bg-yellow px-4 py-2 text-[13px] font-semibold text-navy-deep hover:bg-yellow-hover"
          >
            🎯 View Sniper Deals
          </Link>
          <Link
            href="/catalog"
            className="rounded border border-white/30 px-4 py-2 text-[13px] font-semibold text-white hover:bg-white/10"
          >
            Browse Catalog
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Tracked items" value={num(stats.totalItems)} />
        <StatTile label="Excellent deals" value={num(stats.excellentCount)} hint="≥20% margin" />
        <StatTile label="Top profit potential" value={ils(stats.topProfit)} hint="single item" />
        <StatTile label="Last update" value={shortDate(stats.lastUpdated)} />
      </section>

      {/* Top deals */}
      {topDeals.length > 0 && (
        <section className="mb-8">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-bold">🎯 Top Sniper Deals</h2>
            <Link href="/deals" className="text-[13px] text-link hover:underline">
              View all →
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {topDeals.map((item) => (
              <ItemCard key={item.item_id} item={item} />
            ))}
          </div>
        </section>
      )}

      {/* Themes */}
      <section className="mb-8">
        <h2 className="mb-3 text-lg font-bold">Browse by theme</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
          {THEMES.slice(0, 12).map((theme) => (
            <Link
              key={theme.slug}
              href={`/catalog/themes/${theme.slug}`}
              className="flex items-center gap-2 rounded border border-edge bg-surface px-3 py-2 text-[13px] font-medium hover:border-link hover:text-link"
            >
              <span>{theme.icon}</span>
              {theme.name}
            </Link>
          ))}
        </div>
        <Link href="/catalog" className="mt-2 inline-block text-[13px] text-link hover:underline">
          All themes →
        </Link>
      </section>

      {/* Recently updated */}
      {recent.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-bold">Recently updated</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {recent.map((item) => (
              <ItemCard key={item.item_id} item={item} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
