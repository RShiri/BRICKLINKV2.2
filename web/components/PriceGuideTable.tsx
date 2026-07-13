import type { Guide, GuideSide } from "@/lib/types";
import { ils, num } from "@/lib/format";

function SideRows({ side }: { side: GuideSide }) {
  return (
    <table className="w-full text-[12px]">
      <tbody>
        <tr>
          <td className="py-0.5 pr-2 text-ink-muted">Min:</td>
          <td className="text-right font-medium">{ils(side.min)}</td>
        </tr>
        <tr>
          <td className="py-0.5 pr-2 text-ink-muted">Avg:</td>
          <td className="text-right font-semibold">{ils(side.avg)}</td>
        </tr>
        <tr>
          <td className="py-0.5 pr-2 text-ink-muted">Max:</td>
          <td className="text-right font-medium">{ils(side.max)}</td>
        </tr>
        <tr>
          <td className="py-0.5 pr-2 text-ink-muted">Qty:</td>
          <td className="text-right">{num(side.qty)}</td>
        </tr>
        <tr>
          <td className="py-0.5 pr-2 text-ink-muted">Lots:</td>
          <td className="text-right">{num(side.lots)}</td>
        </tr>
      </tbody>
    </table>
  );
}

/**
 * The classic BrickLink price-guide quadrant: New/Used × Last 6 Months Sales /
 * Current Items for Sale, from analyzer-cleaned listings (items.guide).
 */
export function PriceGuideTable({ guide }: { guide: Guide }) {
  const cells = [
    { title: "New · Sold", tint: "bg-guide-new", side: guide.new.sold },
    { title: "Used · Sold", tint: "bg-guide-used", side: guide.used.sold },
    { title: "New · For Sale", tint: "bg-guide-new", side: guide.new.stock },
    { title: "Used · For Sale", tint: "bg-guide-used", side: guide.used.stock },
  ];
  return (
    <div className="overflow-hidden rounded border border-edge">
      <div className="grid grid-cols-2 border-b border-edge bg-thead text-center text-[12px] font-semibold">
        <div className="border-r border-edge py-1.5">Sales (filtered)</div>
        <div className="py-1.5">Current Items for Sale</div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4">
        {[cells[0], cells[1], cells[2], cells[3]].map((cell, i) => (
          <div
            key={cell.title}
            className={`${cell.tint} ${i < 3 ? "border-r border-edge" : ""} p-3`}
          >
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
              {cell.title}
            </p>
            <SideRows side={cell.side} />
          </div>
        ))}
      </div>
    </div>
  );
}
