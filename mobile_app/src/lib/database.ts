import { supabase } from "./supabase";
import { Minifig } from "../types";

function parseMinifig(row: {
  item_id: string;
  json_data: string;
  cached_rating: string | null;
  cached_profit: number | null;
  cached_margin: number | null;
  updated_at: string;
}): Minifig | null {
  try {
    const data = typeof row.json_data === "string"
      ? JSON.parse(row.json_data)
      : row.json_data;

    const meta = data?.meta ?? {};
    const yr = meta.year_released;
    const yearInt = yr ? parseInt(String(yr), 10) : 0;

    // Best-effort price extraction from first stock listing
    const newPrices = data?.new?.stock ?? [];
    const usedPrices = data?.used?.stock ?? [];
    const newPrice = newPrices.length > 0 ? (newPrices[0]?.price ?? 0) : 0;
    const usedPrice = usedPrices.length > 0 ? (usedPrices[0]?.price ?? 0) : 0;

    return {
      id: row.item_id,
      name: meta.item_name ?? "Unknown",
      year: yearInt > 0 ? String(yearInt) : "Unknown",
      yearInt,
      newPrice,
      usedPrice,
      profit: row.cached_profit ?? 0,
      margin: row.cached_margin ?? 0,
      rating: row.cached_rating ?? "N/A",
      imageUrl: `https://img.bricklink.com/ItemImage/MN/0/${row.item_id}.png`,
      updatedAt: row.updated_at,
    };
  } catch {
    return null;
  }
}

export async function getItemsByPrefix(prefix: string): Promise<Minifig[]> {
  const { data, error } = await supabase
    .from("items")
    .select("item_id, json_data, cached_rating, cached_profit, cached_margin, updated_at")
    .ilike("item_id", `${prefix}%`)
    .order("cached_profit", { ascending: false });

  if (error || !data) return [];

  return data
    .map(parseMinifig)
    .filter((m): m is Minifig => m !== null);
}

export async function searchItems(query: string): Promise<Minifig[]> {
  if (!query.trim()) return [];

  const { data, error } = await supabase
    .from("items")
    .select("item_id, json_data, cached_rating, cached_profit, cached_margin, updated_at")
    .ilike("item_id", `%${query}%`)
    .limit(100);

  if (error || !data) return [];

  const byId = data.map(parseMinifig).filter((m): m is Minifig => m !== null);

  // Also search by name (client-side from already fetched data is too slow for large DB,
  // so we do a second query targeting json_data text)
  const { data: data2 } = await supabase
    .from("items")
    .select("item_id, json_data, cached_rating, cached_profit, cached_margin, updated_at")
    .ilike("json_data", `%"item_name": "%${query}%"%`)
    .limit(100);

  const byName = (data2 ?? [])
    .map(parseMinifig)
    .filter((m): m is Minifig => m !== null);

  // Merge, deduplicate by id
  const seen = new Set(byId.map((m) => m.id));
  const merged = [...byId];
  for (const fig of byName) {
    if (!seen.has(fig.id)) {
      merged.push(fig);
      seen.add(fig.id);
    }
  }
  return merged;
}

export async function getCollectionItems(collectionName: string): Promise<string[]> {
  const { data, error } = await supabase
    .from("collections")
    .select("item_id")
    .eq("collection_name", collectionName);

  if (error || !data) return [];
  return data.map((r: { item_id: string }) => r.item_id.toLowerCase());
}

export async function getCollectionMinifigs(collectionName: string): Promise<Minifig[]> {
  const ids = await getCollectionItems(collectionName);
  if (!ids.length) return [];

  const { data, error } = await supabase
    .from("items")
    .select("item_id, json_data, cached_rating, cached_profit, cached_margin, updated_at")
    .in("item_id", ids);

  if (error || !data) return [];
  return data.map(parseMinifig).filter((m): m is Minifig => m !== null);
}

export async function getDashboardStats(): Promise<{
  totalItems: number;
  excellentDeals: number;
  topProfit: number;
  avgProfit: number;
}> {
  const { count: totalItems } = await supabase
    .from("items")
    .select("*", { count: "exact", head: true });

  const { count: excellentDeals } = await supabase
    .from("items")
    .select("*", { count: "exact", head: true })
    .eq("cached_rating", "EXCELLENT");

  const { data: profitData } = await supabase
    .from("items")
    .select("cached_profit")
    .order("cached_profit", { ascending: false })
    .gt("cached_profit", 0)
    .limit(1);

  const { data: avgData } = await supabase
    .from("items")
    .select("cached_profit")
    .gt("cached_profit", 0);

  const topProfit = profitData?.[0]?.cached_profit ?? 0;
  const avg = avgData
    ? avgData.reduce((s: number, r: { cached_profit: number }) => s + (r.cached_profit ?? 0), 0) / avgData.length
    : 0;

  return {
    totalItems: totalItems ?? 0,
    excellentDeals: excellentDeals ?? 0,
    topProfit,
    avgProfit: Math.round(avg),
  };
}

export async function getTopDeals(limit = 20): Promise<Minifig[]> {
  const { data, error } = await supabase
    .from("items")
    .select("item_id, json_data, cached_rating, cached_profit, cached_margin, updated_at")
    .eq("cached_rating", "EXCELLENT")
    .order("cached_profit", { ascending: false })
    .limit(limit);

  if (error || !data) return [];
  return data.map(parseMinifig).filter((m): m is Minifig => m !== null);
}
