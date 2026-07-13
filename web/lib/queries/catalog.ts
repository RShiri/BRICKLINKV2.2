import { supabasePublic } from "@/lib/supabase/server";
import type { CatalogMinifig, CatalogPart, CatalogSet, Item, Theme } from "@/lib/types";
import { classifyUniverse, type ThemeDef } from "@/lib/theme-prefixes";

export const ITEM_COLUMNS =
  "item_id, item_type, name, year_released, price_new, price_used, " +
  "confidence_new, confidence_used, buy_target, lifecycle, guide, " +
  "cached_rating, cached_profit, cached_margin, updated_at";

export async function getItemsByPrefix(prefix: string): Promise<Item[]> {
  const sb = supabasePublic();
  if (!sb) return [];
  const { data } = await sb
    .from("items")
    .select(ITEM_COLUMNS)
    .like("item_id", `${prefix}%`)
    .order("item_id");
  return (data as unknown as Item[]) ?? [];
}

/** Items for a curated theme, applying the Marvel/DC classifier when set. */
export async function getThemeItems(theme: ThemeDef): Promise<Item[]> {
  const items = await getItemsByPrefix(theme.prefix);
  if (!theme.classifier) return items;
  return items.filter(
    (i) => classifyUniverse(i.item_id, i.name ?? "") === theme.classifier,
  );
}

export async function getItem(itemId: string): Promise<Item | null> {
  const sb = supabasePublic();
  if (!sb) return null;
  const { data } = await sb
    .from("items")
    .select(ITEM_COLUMNS)
    .eq("item_id", itemId)
    .maybeSingle();
  return (data as unknown as Item) ?? null;
}

export async function getCatalogSet(setNum: string): Promise<CatalogSet | null> {
  const sb = supabasePublic();
  if (!sb) return null;
  const rbNum = setNum.includes("-") ? setNum : `${setNum}-1`;
  const { data } = await sb
    .from("catalog_sets")
    .select("set_num, name, year, theme_id, num_parts, img_url")
    .eq("set_num", rbNum)
    .maybeSingle();
  return (data as unknown as CatalogSet) ?? null;
}

export async function getCatalogMinifig(figNum: string): Promise<CatalogMinifig | null> {
  const sb = supabasePublic();
  if (!sb) return null;
  const { data } = await sb
    .from("catalog_minifigs")
    .select("fig_num, name, num_parts, img_url")
    .eq("fig_num", figNum)
    .maybeSingle();
  return (data as unknown as CatalogMinifig) ?? null;
}

export async function getCatalogPart(partNum: string): Promise<CatalogPart | null> {
  const sb = supabasePublic();
  if (!sb) return null;
  const { data } = await sb
    .from("catalog_parts")
    .select("part_num, name, part_cat_id")
    .eq("part_num", partNum)
    .maybeSingle();
  return (data as unknown as CatalogPart) ?? null;
}

export async function getThemePath(themeId: number | null): Promise<Theme[]> {
  const sb = supabasePublic();
  if (!sb || themeId == null) return [];
  const path: Theme[] = [];
  let current: number | null = themeId;
  // Theme trees are at most a few levels deep.
  for (let depth = 0; depth < 5 && current != null; depth++) {
    const result = await sb
      .from("themes")
      .select("id, name, parent_id")
      .eq("id", current)
      .maybeSingle();
    const theme = result.data as unknown as Theme | null;
    if (!theme) break;
    path.unshift(theme);
    current = theme.parent_id;
  }
  return path;
}

/** Rebrickable id for a BrickLink item, via external_id_map. */
export async function rbIdFor(itemType: "set" | "minifig", extId: string): Promise<string | null> {
  const sb = supabasePublic();
  if (!sb) return null;
  const { data } = await sb
    .from("external_id_map")
    .select("rb_id")
    .eq("provider", "bricklink")
    .eq("item_type", itemType)
    .eq("ext_id", extId)
    .maybeSingle();
  return data?.rb_id ?? null;
}

/** BrickLink id for a Rebrickable id (reverse lookup). */
export async function blIdFor(itemType: "set" | "minifig", rbId: string): Promise<string | null> {
  const sb = supabasePublic();
  if (!sb) return null;
  const { data } = await sb
    .from("external_id_map")
    .select("ext_id")
    .eq("provider", "bricklink")
    .eq("item_type", itemType)
    .eq("rb_id", rbId)
    .limit(1)
    .maybeSingle();
  return data?.ext_id ?? null;
}

export type SetMinifigEntry = {
  fig_num: string;
  name: string;
  quantity: number;
  img_url: string | null;
  bl_id: string | null;
  item: Item | null;
};

/** Minifigs contained in a set (Rebrickable inventory), joined to prices. */
export async function getSetMinifigs(setNum: string): Promise<SetMinifigEntry[]> {
  const sb = supabasePublic();
  if (!sb) return [];
  const rbNum = setNum.includes("-") ? setNum : `${setNum}-1`;

  const { data: inv } = await sb
    .from("inventories")
    .select("id")
    .eq("set_num", rbNum)
    .order("version", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (!inv) return [];

  const { data: figs } = await sb
    .from("inventory_minifigs")
    .select("fig_num, quantity, catalog_minifigs(name, img_url)")
    .eq("inventory_id", inv.id);
  if (!figs?.length) return [];

  const figNums = figs.map((f) => f.fig_num);
  const { data: mappings } = await sb
    .from("external_id_map")
    .select("rb_id, ext_id")
    .eq("provider", "bricklink")
    .eq("item_type", "minifig")
    .in("rb_id", figNums);
  const blByRb = new Map((mappings ?? []).map((m) => [m.rb_id, m.ext_id]));

  const blIds = [...blByRb.values()];
  let itemsById = new Map<string, Item>();
  if (blIds.length) {
    const { data: items } = await sb.from("items").select(ITEM_COLUMNS).in("item_id", blIds);
    itemsById = new Map(((items as unknown as Item[]) ?? []).map((i) => [i.item_id, i]));
  }

  return figs.map((f) => {
    const cat = f.catalog_minifigs as unknown as { name: string; img_url: string | null } | null;
    const blId = blByRb.get(f.fig_num) ?? null;
    return {
      fig_num: f.fig_num,
      name: cat?.name ?? f.fig_num,
      quantity: f.quantity,
      img_url: cat?.img_url ?? null,
      bl_id: blId,
      item: blId ? (itemsById.get(blId) ?? null) : null,
    };
  });
}

export type SetPartEntry = {
  part_num: string;
  color_id: number;
  quantity: number;
  is_spare: boolean;
  img_url: string | null;
  name: string;
  color_name: string;
  color_rgb: string | null;
};

/**
 * Part inventory for a set or minifig (Rebrickable models fig inventories
 * as set_num = "fig-…"). No FKs exist from inventory_parts to
 * catalog_parts/colors, so names and colors are stitched in manually.
 */
export async function getInventoryParts(refNum: string): Promise<SetPartEntry[]> {
  const sb = supabasePublic();
  if (!sb) return [];
  const rbNum = refNum.includes("-") ? refNum : `${refNum}-1`;

  const { data: inv } = await sb
    .from("inventories")
    .select("id")
    .eq("set_num", rbNum)
    .order("version", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (!inv) return [];

  const { data: rows } = await sb
    .from("inventory_parts")
    .select("part_num, color_id, quantity, is_spare, img_url")
    .eq("inventory_id", inv.id)
    .order("is_spare", { ascending: true })
    .order("quantity", { ascending: false })
    .limit(3000);
  if (!rows?.length) return [];

  const partNums = [...new Set(rows.map((r) => r.part_num))];
  const nameByPart = new Map<string, string>();
  // .in() lists go through the URL; chunk to stay under length limits.
  for (let i = 0; i < partNums.length; i += 200) {
    const { data: parts } = await sb
      .from("catalog_parts")
      .select("part_num, name")
      .in("part_num", partNums.slice(i, i + 200));
    for (const p of parts ?? []) nameByPart.set(p.part_num, p.name);
  }

  const colorIds = [...new Set(rows.map((r) => r.color_id))];
  const { data: colors } = await sb.from("colors").select("id, name, rgb").in("id", colorIds);
  const colorById = new Map((colors ?? []).map((c) => [c.id, c]));

  return rows.map((r) => ({
    ...r,
    name: nameByPart.get(r.part_num) ?? r.part_num,
    color_name: colorById.get(r.color_id)?.name ?? "—",
    color_rgb: colorById.get(r.color_id)?.rgb ?? null,
  }));
}

/** Sets a minifig appears in (reverse inventory lookup). */
export async function getFigAppearsIn(figNum: string): Promise<CatalogSet[]> {
  const sb = supabasePublic();
  if (!sb) return [];
  const { data: invRows } = await sb
    .from("inventory_minifigs")
    .select("inventory_id")
    .eq("fig_num", figNum)
    .limit(50);
  if (!invRows?.length) return [];
  const { data: invs } = await sb
    .from("inventories")
    .select("set_num")
    .in("id", invRows.map((r) => r.inventory_id));
  const setNums = [...new Set((invs ?? []).map((i) => i.set_num))].filter(
    (s) => !s.startsWith("fig-"),
  );
  if (!setNums.length) return [];
  const { data: sets } = await sb
    .from("catalog_sets")
    .select("set_num, name, year, theme_id, num_parts, img_url")
    .in("set_num", setNums)
    .order("year", { ascending: false });
  return (sets as unknown as CatalogSet[]) ?? [];
}

export type HomeStats = {
  totalItems: number;
  excellentCount: number;
  topProfit: number;
  lastUpdated: string | null;
};

export async function getHomeStats(): Promise<HomeStats> {
  const sb = supabasePublic();
  const empty = { totalItems: 0, excellentCount: 0, topProfit: 0, lastUpdated: null };
  if (!sb) return empty;
  const [{ count: totalItems }, { count: excellentCount }, { data: top }, { data: latest }] =
    await Promise.all([
      sb.from("items").select("item_id", { count: "exact", head: true }),
      sb
        .from("items")
        .select("item_id", { count: "exact", head: true })
        .eq("cached_rating", "EXCELLENT"),
      sb
        .from("items")
        .select("cached_profit")
        .order("cached_profit", { ascending: false })
        .limit(1)
        .maybeSingle(),
      sb
        .from("items")
        .select("updated_at")
        .order("updated_at", { ascending: false })
        .limit(1)
        .maybeSingle(),
    ]);
  return {
    totalItems: totalItems ?? 0,
    excellentCount: excellentCount ?? 0,
    topProfit: top?.cached_profit ?? 0,
    lastUpdated: latest?.updated_at ?? null,
  };
}

export async function getRecentlyUpdated(limit = 12): Promise<Item[]> {
  const sb = supabasePublic();
  if (!sb) return [];
  const { data } = await sb
    .from("items")
    .select(ITEM_COLUMNS)
    .not("name", "is", null)
    .order("updated_at", { ascending: false })
    .limit(limit);
  return (data as unknown as Item[]) ?? [];
}
