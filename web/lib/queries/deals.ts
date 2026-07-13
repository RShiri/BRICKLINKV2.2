import { supabasePublic } from "@/lib/supabase/server";
import { ITEM_COLUMNS } from "@/lib/queries/catalog";
import type { Item, Rating } from "@/lib/types";

export type DealFilters = {
  rating?: Rating | "ALL";
  minMargin?: number;
  last24h?: boolean;
  prefix?: string;
  limit?: number;
};

/** Sniper War Room: rated deals over the cached analyzer columns. */
export async function getDeals(filters: DealFilters = {}): Promise<Item[]> {
  const sb = supabasePublic();
  if (!sb) return [];
  let query = sb
    .from("items")
    .select(ITEM_COLUMNS)
    .gt("cached_profit", 0)
    .order("cached_profit", { ascending: false })
    .limit(filters.limit ?? 100);

  if (filters.rating && filters.rating !== "ALL") {
    query = query.eq("cached_rating", filters.rating);
  } else {
    query = query.in("cached_rating", ["EXCELLENT", "GREAT INVEST", "GOOD"]);
  }
  if (filters.minMargin) query = query.gte("cached_margin", filters.minMargin);
  if (filters.last24h) {
    const since = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
    query = query.gte("updated_at", since);
  }
  if (filters.prefix) query = query.like("item_id", `${filters.prefix}%`);

  const { data } = await query;
  return (data as unknown as Item[]) ?? [];
}

export async function getTopDeals(limit = 8): Promise<Item[]> {
  return getDeals({ rating: "EXCELLENT", limit });
}
