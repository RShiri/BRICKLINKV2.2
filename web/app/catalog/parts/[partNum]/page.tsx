import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getCatalogPart } from "@/lib/queries/catalog";
import { supabasePublic } from "@/lib/supabase/server";
import { Breadcrumbs } from "@/components/Breadcrumbs";

type Params = { partNum: string };

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { partNum } = await params;
  return { title: `Part ${decodeURIComponent(partNum)}` };
}

export default async function PartPage({ params }: { params: Promise<Params> }) {
  const { partNum: raw } = await params;
  const partNum = decodeURIComponent(raw);
  const part = await getCatalogPart(partNum);
  if (!part) notFound();

  const sb = supabasePublic();
  let colors: { name: string; rgb: string | null }[] = [];
  let category: string | null = null;
  if (sb) {
    const [{ data: colorRows }, { data: cat }] = await Promise.all([
      sb
        .from("inventory_parts")
        .select("color_id, colors:color_id(name, rgb)")
        .eq("part_num", partNum)
        .limit(400),
      part.part_cat_id
        ? sb.from("part_categories").select("name").eq("id", part.part_cat_id).maybeSingle()
        : Promise.resolve({ data: null }),
    ]);
    const seen = new Map<string, { name: string; rgb: string | null }>();
    for (const row of colorRows ?? []) {
      const c = row.colors as unknown as { name: string; rgb: string | null } | null;
      if (c && !seen.has(c.name)) seen.set(c.name, c);
    }
    colors = [...seen.values()];
    category = (cat as { name: string } | null)?.name ?? null;
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs
        crumbs={[{ label: "Catalog", href: "/catalog" }, { label: "Parts" }, { label: partNum }]}
      />
      <h1 className="mb-1 text-xl font-bold">{part.name}</h1>
      <p className="mb-6 font-mono text-[13px] text-ink-muted">
        {partNum}
        {category ? ` · ${category}` : ""}
      </p>

      <section className="mb-6">
        <h2 className="mb-2 text-base font-bold">Available colors ({colors.length})</h2>
        <div className="flex flex-wrap gap-1.5">
          {colors.map((c) => (
            <span
              key={c.name}
              className="flex items-center gap-1.5 rounded border border-edge bg-surface px-2 py-1 text-[12px]"
            >
              <span
                className="h-3 w-3 rounded-full border border-edge"
                style={{ background: c.rgb ? `#${c.rgb}` : "#ccc" }}
              />
              {c.name}
            </span>
          ))}
          {colors.length === 0 && <p className="text-[13px] text-ink-muted">No color data.</p>}
        </div>
      </section>

      <p className="rounded border border-dashed border-edge p-4 text-[13px] text-ink-muted">
        Part-level market prices are not tracked yet — the price engine currently covers sets
        and minifigures.
      </p>
    </div>
  );
}
