import { supabaseServer } from "@/lib/supabase/server";
import { ITEM_COLUMNS } from "@/lib/queries/catalog";
import type { Item } from "@/lib/types";

export type CollectionEntry = { item: Item; added_at: string };

export async function getMyCollection(): Promise<CollectionEntry[]> {
  const sb = await supabaseServer();
  if (!sb) return [];
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return [];

  const { data: rows } = await sb
    .from("user_collections")
    .select("item_id, added_at")
    .eq("user_id", user.id)
    .order("added_at", { ascending: false });
  if (!rows?.length) return [];

  const { data: items } = await sb
    .from("items")
    .select(ITEM_COLUMNS)
    .in("item_id", rows.map((r) => r.item_id));
  const byId = new Map(((items as unknown as Item[]) ?? []).map((i) => [i.item_id, i]));

  return rows
    .map((r) => {
      const item = byId.get(r.item_id);
      return item ? { item, added_at: r.added_at } : null;
    })
    .filter((x): x is CollectionEntry => x != null);
}

export async function isInMyCollection(itemId: string): Promise<boolean | null> {
  const sb = await supabaseServer();
  if (!sb) return null;
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return null;
  const { data } = await sb
    .from("user_collections")
    .select("item_id")
    .eq("user_id", user.id)
    .eq("item_id", itemId)
    .maybeSingle();
  return data != null;
}
