import type { Metadata } from "next";
import { Breadcrumbs } from "@/components/Breadcrumbs";

export const metadata: Metadata = { title: "Price Guide Methodology" };

const STEPS = [
  {
    title: "1. Completeness filter",
    body: "Listings flagged incomplete, or whose descriptions contain red flags ('no minifigs', 'build only', 'missing parts', …), are removed before any math happens.",
  },
  {
    title: "2. Minifig price floor (used sets)",
    body: "A used set priced below 80% of its minifigures' combined value is almost always incomplete — those listings are dropped.",
  },
  {
    title: "3. Dynamic price floor",
    body: "Listings below 20% of the global median are treated as box-only/instructions-only noise and removed (relaxed for very new, volatile sets).",
  },
  {
    title: "4. Bulk-seller filter",
    body: "Lots with quantity above 3 are wholesale offers, not collector-market prices, and are excluded.",
  },
  {
    title: "5. IQR outlier removal",
    body: "With at least 5 clean listings, prices outside 1.5×IQR of the interquartile range are cut. The central value used is the median, which resists manipulation better than a mean.",
  },
  {
    title: "6. Confidence-weighted market price",
    body: "With 10+ sales: 70% sold-median + 30% competitive stock anchor (HIGH confidence). With 2–9 sales: 60/40 blend (MEDIUM). Fewer: stock anchor only (LOW). The stock anchor is the median of the cheapest half of current listings. Confidence is downgraded when more than 30% of raw data was filtered.",
  },
  {
    title: "7. Deal rating",
    body: "The cheapest surviving listing is compared to market price. Profit assumes 13% marketplace fees. Margin ≥20% → EXCELLENT; ≥10% → GOOD; a GOOD deal on a retired/end-of-life set → GREAT INVEST.",
  },
];

export default function PriceGuidePage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <Breadcrumbs crumbs={[{ label: "Price Guide" }]} />
      <h1 className="mb-1 text-xl font-bold">How our prices are computed</h1>
      <p className="mb-6 text-[13px] text-ink-muted">
        Raw marketplace data is noisy: incomplete sets, box-only listings, bulk lots, and
        outliers distort simple averages. Every price on this site goes through a
        multi-layer statistical pipeline first. All prices are shown in ₪ (ILS).
      </p>

      <ol className="space-y-3">
        {STEPS.map((step) => (
          <li key={step.title} className="rounded border border-edge bg-surface p-4">
            <p className="font-semibold">{step.title}</p>
            <p className="mt-1 text-[13px] text-ink-muted">{step.body}</p>
          </li>
        ))}
      </ol>

      <div className="mt-6 rounded border border-edge bg-guide-new p-4 text-[13px]">
        <p className="font-semibold">Reading the price-guide quadrant</p>
        <p className="mt-1 text-ink-muted">
          Each item page shows the classic four-cell guide: <strong>New</strong> and{" "}
          <strong>Used</strong> crossed with <strong>Sales</strong> (what buyers actually
          paid) and <strong>Current Items for Sale</strong> (what sellers are asking).
          Min/Avg/Max are computed from filtered listings only; Qty counts units and Lots
          counts distinct listings. The <strong>buy target</strong> is 80% of fair market —
          paying below it historically leaves room for fees and profit.
        </p>
      </div>
    </div>
  );
}
