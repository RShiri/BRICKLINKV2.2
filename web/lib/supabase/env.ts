/**
 * Supabase connection env. The dashboard now issues "publishable" keys
 * (sb_publishable_...) as the drop-in replacement for the legacy anon JWT,
 * and its setup snippets name the var accordingly — accept either name.
 * Both references stay statically analyzable so Next can inline them into
 * client bundles.
 */
export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
export const SUPABASE_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
