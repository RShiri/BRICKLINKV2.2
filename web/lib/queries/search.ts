import { supabasePublic } from "@/lib/supabase/server";
import type { SearchResult } from "@/lib/types";

export type SearchScope = "all" | "sets" | "parts" | "minifigs";

export async function searchCatalog(
  q: string,
  scope: SearchScope = "all",
  limit = 10,
): Promise<SearchResult[]> {
  const sb = supabasePublic();
  if (!sb || q.trim().length < 2) return [];
  const { data, error } = await sb.rpc("search_catalog", {
    q: q.trim(),
    scope,
    lim: limit,
  });
  if (error) return [];
  return (data as unknown as SearchResult[]) ?? [];
}
