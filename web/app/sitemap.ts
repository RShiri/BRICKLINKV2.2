import type { MetadataRoute } from "next";
import { THEMES } from "@/lib/theme-prefixes";
import { SITE_URL } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const statics: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, changeFrequency: "hourly", priority: 1 },
    { url: `${SITE_URL}/deals`, changeFrequency: "hourly", priority: 0.9 },
    { url: `${SITE_URL}/catalog`, changeFrequency: "daily", priority: 0.8 },
    { url: `${SITE_URL}/price-guide`, changeFrequency: "monthly", priority: 0.5 },
    { url: `${SITE_URL}/search`, changeFrequency: "monthly", priority: 0.3 },
  ];

  const themes: MetadataRoute.Sitemap = THEMES.map((t) => ({
    url: `${SITE_URL}/catalog/themes/${t.slug}`,
    changeFrequency: "daily",
    priority: 0.7,
  }));

  return [...statics, ...themes];
}
