/**
 * Canonical site origin for absolute URLs (sitemap, robots, OG metadata).
 * Set NEXT_PUBLIC_SITE_URL in production (e.g. https://bricksniper.vercel.app);
 * Vercel's own URL is used as a fallback on preview deploys.
 */
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000");
