import Link from "next/link";
import type { Item } from "@/lib/types";
import { blImageUrl, ils, pct } from "@/lib/format";
import { DealBadge, ConfidencePill } from "@/components/Badges";
import { itemHref } from "@/components/ItemCard";

/**
 * Dense BrickLink-style item table. Sorting is server-side: header links
 * rewrite the `sort` search param on the current path.
 */
export function ItemTable({
  items,
  basePath,
  currentSort,
  searchParams,
}: {
  items: Item[];
  basePath: string;
  currentSort: string;
  searchParams: Record<string, string | undefined>;
}) {
  const headers: { key: string; label: string; numeric?: boolean }[] = [
    { key: "", label: "Image" },
    { key: "item_id", label: "ID" },
    { key: "name", label: "Name" },
    { key: "year", label: "Year", numeric: true },
    { key: "new", label: "New ₪", numeric: true },
    { key: "used", label: "Used ₪", numeric: true },
    { key: "profit", label: "Profit ₪", numeric: true },
    { key: "margin", label: "Margin", numeric: true },
    { key: "", label: "Rating" },
    { key: "", label: "Conf." },
  ];

  function sortHref(key: string): string {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(searchParams)) {
      if (v != null && k !== "sort") params.set(k, v);
    }
    params.set("sort", currentSort === key ? `-${key}` : key);
    return `${basePath}?${params.toString()}`;
  }

  return (
    <div className="overflow-x-auto rounded border border-edge bg-surface">
      <table className="table-dense w-full">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} className={h.numeric ? "text-right" : ""}>
                {h.key ? (
                  <Link href={sortHref(h.key)} className="hover:text-link">
                    {h.label}
                    {currentSort === h.key ? " ↑" : currentSort === `-${h.key}` ? " ↓" : ""}
                  </Link>
                ) : (
                  h.label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.item_id}>
              <td className="w-14">
                <div className="flex h-10 w-12 items-center justify-center overflow-hidden rounded bg-white">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={blImageUrl(item.item_id)}
                    alt=""
                    loading="lazy"
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
              </td>
              <td className="font-mono text-[12px]">
                <Link href={itemHref(item)} className="text-link hover:underline">
                  {item.item_id}
                </Link>
              </td>
              <td className="max-w-[28ch]">
                <Link href={itemHref(item)} className="line-clamp-1 hover:text-link">
                  {item.name ?? item.item_id}
                </Link>
              </td>
              <td className="text-right">{item.year_released ?? "—"}</td>
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
              <td>
                <DealBadge rating={item.cached_rating} />
              </td>
              <td>
                <ConfidencePill confidence={item.confidence_new} />
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={10} className="py-8 text-center text-ink-muted">
                No items found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

/** Shared server-side sorter matching ItemTable's sort keys. */
export function sortItems(items: Item[], sort: string): Item[] {
  const desc = sort.startsWith("-");
  const key = desc ? sort.slice(1) : sort;
  const value = (i: Item): string | number => {
    switch (key) {
      case "item_id": return i.item_id;
      case "name": return i.name ?? "";
      case "year": return i.year_released ?? 0;
      case "new": return i.price_new ?? 0;
      case "used": return i.price_used ?? 0;
      case "profit": return i.cached_profit ?? 0;
      case "margin": return i.cached_margin ?? 0;
      default: return i.item_id;
    }
  };
  const sorted = [...items].sort((a, b) => {
    const av = value(a);
    const bv = value(b);
    if (typeof av === "string" || typeof bv === "string") {
      return String(av).localeCompare(String(bv));
    }
    return av - bv;
  });
  return desc ? sorted.reverse() : sorted;
}
