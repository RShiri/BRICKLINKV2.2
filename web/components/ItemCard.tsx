import Link from "next/link";
import type { Item } from "@/lib/types";
import { blImageUrl, ils } from "@/lib/format";
import { DealBadge } from "@/components/Badges";

export function itemHref(item: Pick<Item, "item_id" | "item_type">): string {
  return item.item_type === "set"
    ? `/catalog/sets/${encodeURIComponent(item.item_id)}`
    : `/catalog/minifigs/${encodeURIComponent(item.item_id)}`;
}

export function ItemCard({ item }: { item: Item }) {
  return (
    <Link
      href={itemHref(item)}
      className="group flex flex-col rounded border border-edge bg-surface p-3 transition-shadow hover:shadow-md"
    >
      <div className="mb-2 flex h-28 items-center justify-center overflow-hidden rounded bg-white">
        {/* BrickLink CDN images have unknown dimensions; plain img keeps this simple */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={blImageUrl(item.item_id)}
          alt={item.name ?? item.item_id}
          loading="lazy"
          className="max-h-full max-w-full object-contain transition-transform group-hover:scale-105"
        />
      </div>
      <p className="font-mono text-[11px] text-ink-muted">{item.item_id}</p>
      <p className="line-clamp-2 min-h-[2.5em] text-[13px] font-medium text-ink">
        {item.name ?? item.item_id}
      </p>
      <div className="mt-auto flex items-center justify-between pt-2">
        <span className="text-[13px] font-semibold text-ink">
          {item.price_new && item.price_new > 0 ? ils(item.price_new) : "—"}
        </span>
        <DealBadge rating={item.cached_rating} />
      </div>
    </Link>
  );
}
