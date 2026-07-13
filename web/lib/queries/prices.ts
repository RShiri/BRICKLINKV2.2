import { supabasePublic } from "@/lib/supabase/server";
import type { PricePoint } from "@/lib/types";

export async function getPriceHistory(itemId: string, days = 90): Promise<PricePoint[]> {
  const sb = supabasePublic();
  if (!sb) return [];
  const since = new Date(Date.now() - days * 24 * 3600 * 1000).toISOString();
  const { data } = await sb
    .from("price_history")
    .select("price_new, price_used, scraped_at")
    .eq("item_id", itemId)
    .gte("scraped_at", since)
    .order("scraped_at");
  return (data as unknown as PricePoint[]) ?? [];
}

export type PriceTrend = { changePct: number; days: number } | null;

export async function getPriceTrend(itemId: string, days = 90): Promise<PriceTrend> {
  const history = await getPriceHistory(itemId, days);
  const priced = history.filter((p) => (p.price_new ?? 0) > 0);
  if (priced.length < 2) return null;
  const first = priced[0].price_new!;
  const last = priced[priced.length - 1].price_new!;
  if (first <= 0) return null;
  return { changePct: ((last - first) / first) * 100, days };
}
