import { NextResponse } from "next/server";
import { themeBySlug } from "@/lib/theme-prefixes";
import { getThemeItems } from "@/lib/queries/catalog";

function csvEscape(value: unknown): string {
  const s = value == null ? "" : String(value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> },
) {
  const { slug } = await params;
  const theme = themeBySlug(slug);
  if (!theme) return new NextResponse("Unknown theme", { status: 404 });

  const items = await getThemeItems(theme);
  const header = [
    "item_id", "name", "year", "price_new_ils", "price_used_ils",
    "confidence_new", "profit_ils", "margin_pct", "rating",
  ];
  const lines = [header.join(",")];
  for (const i of items) {
    lines.push(
      [
        i.item_id, i.name, i.year_released, i.price_new, i.price_used,
        i.confidence_new, i.cached_profit, i.cached_margin, i.cached_rating,
      ]
        .map(csvEscape)
        .join(","),
    );
  }

  return new NextResponse(lines.join("\n"), {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${slug}-minifigs.csv"`,
    },
  });
}
