import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Private or side-effectful surfaces; catalog pages stay crawlable.
      disallow: ["/api/", "/admin", "/collection", "/login", "/tools/"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
