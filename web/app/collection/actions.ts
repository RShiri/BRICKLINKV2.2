"use server";

import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";

export async function addToCollection(itemId: string): Promise<void> {
  const sb = await supabaseServer();
  if (!sb) return;
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return;
  await sb.from("user_collections").upsert({
    user_id: user.id,
    collection_name: "main",
    item_id: itemId,
  });
  revalidatePath("/collection");
}

export async function removeFromCollection(itemId: string): Promise<void> {
  const sb = await supabaseServer();
  if (!sb) return;
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return;
  await sb.from("user_collections").delete().eq("user_id", user.id).eq("item_id", itemId);
  revalidatePath("/collection");
}

export async function signOut(): Promise<void> {
  const sb = await supabaseServer();
  if (!sb) return;
  await sb.auth.signOut();
  revalidatePath("/", "layout");
}
