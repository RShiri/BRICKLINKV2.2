import Link from "next/link";
import type { Metadata } from "next";
import { THEMES } from "@/lib/theme-prefixes";
import { Breadcrumbs } from "@/components/Breadcrumbs";

export const metadata: Metadata = { title: "Catalog" };

export default function CatalogPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs crumbs={[{ label: "Catalog" }]} />
      <h1 className="mb-1 text-xl font-bold">Catalog</h1>
      <p className="mb-6 text-[13px] text-ink-muted">
        Browse tracked minifigure themes with live market prices. Set and part pages are
        reachable through search and item links.
      </p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {THEMES.map((theme) => (
          <Link
            key={theme.slug}
            href={`/catalog/themes/${theme.slug}`}
            className="group flex items-start gap-3 rounded border border-edge bg-surface p-4 transition-shadow hover:shadow-md"
          >
            <span className="text-2xl">{theme.icon}</span>
            <span>
              <span className="block font-semibold text-ink group-hover:text-link">
                {theme.name}
              </span>
              <span className="block text-[12px] text-ink-muted">{theme.description}</span>
              <span className="mt-1 block font-mono text-[11px] text-ink-muted">
                prefix: {theme.prefix}
                {theme.classifier ? ` · ${theme.classifier} filter` : ""}
              </span>
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
