import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { themeBySlug } from "@/lib/theme-prefixes";
import { getThemeItems } from "@/lib/queries/catalog";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ItemTable, sortItems } from "@/components/ItemTable";
import { ItemCard } from "@/components/ItemCard";
import { StatTile } from "@/components/StatTile";
import { ils, num } from "@/lib/format";
import type { Item } from "@/lib/types";

type Params = { slug: string };
type Search = { [key: string]: string | undefined };

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { slug } = await params;
  const theme = themeBySlug(slug);
  return { title: theme ? `${theme.name} Minifigures` : "Theme" };
}

const RATINGS = ["ALL", "EXCELLENT", "GREAT INVEST", "GOOD", "IRRELEVANT"] as const;

function applyFilters(items: Item[], sp: Search): Item[] {
  let out = items;
  const q = sp.q?.toLowerCase();
  if (q) {
    out = out.filter(
      (i) => i.item_id.toLowerCase().includes(q) || (i.name ?? "").toLowerCase().includes(q),
    );
  }
  if (sp.year && sp.year !== "ALL") {
    out = out.filter((i) => String(i.year_released) === sp.year);
  }
  if (sp.rating && sp.rating !== "ALL") {
    out = out.filter((i) => i.cached_rating === sp.rating);
  }
  return out;
}

export default async function ThemePage({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<Search>;
}) {
  const { slug } = await params;
  const sp = await searchParams;
  const theme = themeBySlug(slug);
  if (!theme) notFound();

  const allItems = await getThemeItems(theme);
  const filtered = applyFilters(allItems, sp);
  const sort = sp.sort ?? "-new";
  const items = sortItems(filtered, sort);
  const view = sp.view === "gallery" ? "gallery" : "table";
  const basePath = `/catalog/themes/${slug}`;

  const priced = allItems.filter((i) => (i.price_new ?? 0) > 0);
  const totalNew = priced.reduce((s, i) => s + (i.price_new ?? 0), 0);
  const excellent = allItems.filter((i) => i.cached_rating === "EXCELLENT").length;
  const years = [...new Set(allItems.map((i) => i.year_released).filter(Boolean))].sort(
    (a, b) => Number(b) - Number(a),
  );

  function linkWith(overrides: Record<string, string | undefined>): string {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries({ ...sp, ...overrides })) {
      if (v) p.set(k, v);
    }
    const qs = p.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  }

  const csvHref = `/api/export/theme/${slug}`;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs crumbs={[{ label: "Catalog", href: "/catalog" }, { label: theme.name }]} />
      <h1 className="mb-1 text-xl font-bold">
        {theme.icon} {theme.name}
      </h1>
      <p className="mb-4 text-[13px] text-ink-muted">{theme.description}</p>

      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Figures tracked" value={num(allItems.length)} />
        <StatTile label="Total value (new)" value={ils(totalNew)} />
        <StatTile label="Excellent deals" value={num(excellent)} />
        <StatTile
          label="Avg price (new)"
          value={priced.length ? ils(totalNew / priced.length) : "—"}
        />
      </div>

      {/* Filters */}
      <form method="get" className="mb-3 flex flex-wrap items-end gap-2 text-[13px]">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase text-ink-muted">Search</span>
          <input
            name="q"
            defaultValue={sp.q ?? ""}
            placeholder="Name or ID…"
            className="rounded border border-edge bg-surface px-2 py-1.5"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase text-ink-muted">Year</span>
          <select name="year" defaultValue={sp.year ?? "ALL"} className="rounded border border-edge bg-surface px-2 py-1.5">
            <option value="ALL">All years</option>
            {years.map((y) => (
              <option key={y} value={String(y)}>{y}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase text-ink-muted">Rating</span>
          <select name="rating" defaultValue={sp.rating ?? "ALL"} className="rounded border border-edge bg-surface px-2 py-1.5">
            {RATINGS.map((r) => (
              <option key={r} value={r}>{r === "ALL" ? "All ratings" : r}</option>
            ))}
          </select>
        </label>
        {sp.sort && <input type="hidden" name="sort" value={sp.sort} />}
        {sp.view && <input type="hidden" name="view" value={sp.view} />}
        <button
          type="submit"
          className="rounded bg-blue px-3 py-1.5 font-semibold text-white hover:opacity-90"
        >
          Apply
        </button>
        <span className="ml-auto flex items-center gap-2">
          <Link
            href={linkWith({ view: undefined })}
            className={`rounded px-2 py-1 ${view === "table" ? "bg-navy text-white" : "border border-edge"}`}
          >
            Table
          </Link>
          <Link
            href={linkWith({ view: "gallery" })}
            className={`rounded px-2 py-1 ${view === "gallery" ? "bg-navy text-white" : "border border-edge"}`}
          >
            Gallery
          </Link>
          <a href={csvHref} className="rounded border border-edge px-2 py-1 hover:text-link">
            ⬇ CSV
          </a>
        </span>
      </form>

      <p className="mb-2 text-[12px] text-ink-muted">
        {num(items.length)} of {num(allItems.length)} items
      </p>

      {view === "gallery" ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {items.map((item) => (
            <ItemCard key={item.item_id} item={item} />
          ))}
        </div>
      ) : (
        <ItemTable items={items} basePath={basePath} currentSort={sort} searchParams={sp} />
      )}
    </div>
  );
}
