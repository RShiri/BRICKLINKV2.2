import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { SUPABASE_URL, SUPABASE_KEY } from "@/lib/supabase/env";

/**
 * Anonymous client for public data (catalog, prices, deals). No cookies, so
 * it is usable anywhere on the server. Returns null when env vars are absent
 * (e.g. CI builds without secrets) — queries degrade to empty results.
 */
export function supabasePublic(): SupabaseClient | null {
  const url = SUPABASE_URL;
  const key = SUPABASE_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { persistSession: false } });
}

/** Cookie-aware client for authenticated requests (collections, jobs). */
export async function supabaseServer() {
  const url = SUPABASE_URL;
  const key = SUPABASE_KEY;
  if (!url || !key) return null;
  const cookieStore = await cookies();
  return createServerClient(url, key, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options),
          );
        } catch {
          // Called from a Server Component: middleware refreshes sessions.
        }
      },
    },
  });
}
