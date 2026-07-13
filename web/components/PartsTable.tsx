import Link from "next/link";
import { ItemImage } from "@/components/ItemImage";
import { num } from "@/lib/format";
import type { SetPartEntry } from "@/lib/queries/catalog";

/** Dense part-inventory table for set and minifig pages. */
export function PartsTable({ parts }: { parts: SetPartEntry[] }) {
  const regular = parts.filter((p) => !p.is_spare);
  const spares = parts.length - regular.length;
  const pieces = regular.reduce((s, p) => s + p.quantity, 0);

  return (
    <div className="rounded border border-edge bg-surface">
      <div className="max-h-[32rem] overflow-auto">
        <table className="table-dense w-full">
          <thead>
            <tr>
              <th>Image</th>
              <th>Part</th>
              <th>Name</th>
              <th>Color</th>
              <th className="text-right">Qty</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {parts.map((p) => (
              <tr key={`${p.part_num}/${p.color_id}/${p.is_spare ? "s" : "n"}`}>
                <td className="w-12">
                  <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded bg-white">
                    <ItemImage
                      src={p.img_url}
                      alt=""
                      loading="lazy"
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                </td>
                <td className="font-mono text-[12px]">
                  <Link
                    href={`/catalog/parts/${encodeURIComponent(p.part_num)}`}
                    className="text-link hover:underline"
                  >
                    {p.part_num}
                  </Link>
                </td>
                <td className="max-w-[26rem]">
                  <span className="line-clamp-1">{p.name}</span>
                </td>
                <td className="whitespace-nowrap">
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      className="h-3.5 w-3.5 shrink-0 rounded-sm border border-edge"
                      style={
                        p.color_rgb ? { backgroundColor: `#${p.color_rgb}` } : undefined
                      }
                    />
                    <span className="text-[12px]">{p.color_name}</span>
                  </span>
                </td>
                <td className="text-right font-medium">{p.quantity}</td>
                <td>
                  {p.is_spare && (
                    <span className="rounded bg-surface-2 px-1.5 py-0.5 text-[11px] text-ink-muted">
                      spare
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="border-t border-edge px-3 py-2 text-[12px] text-ink-muted">
        {num(pieces)} pieces across {num(regular.length)} lots
        {spares > 0 ? ` · ${num(spares)} spare lots` : ""}
      </p>
    </div>
  );
}
