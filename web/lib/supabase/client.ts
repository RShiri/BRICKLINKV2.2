"use client";

import { createBrowserClient } from "@supabase/ssr";
import { SUPABASE_URL, SUPABASE_KEY } from "@/lib/supabase/env";

export function supabaseBrowser() {
  return createBrowserClient(SUPABASE_URL!, SUPABASE_KEY!);
}
