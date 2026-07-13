import type { Confidence, Lifecycle, Rating } from "@/lib/types";

const RATING_STYLES: Record<string, string> = {
  EXCELLENT: "bg-[#16A34A] text-white",
  "GREAT INVEST": "bg-[#7C3AED] text-white",
  GOOD: "bg-[#2563EB] text-white",
  IRRELEVANT: "bg-[#9CA3AF] text-white",
};

export function DealBadge({ rating }: { rating: Rating | null | undefined }) {
  if (!rating || rating === "N/A") return null;
  return (
    <span
      className={`inline-block rounded px-1.5 py-0.5 text-[11px] font-semibold ${
        RATING_STYLES[rating] ?? "bg-surface-2 text-ink-muted"
      }`}
    >
      {rating}
    </span>
  );
}

const CONFIDENCE_STYLES: Record<string, string> = {
  HIGH: "border-[#16A34A] text-[#16A34A]",
  MEDIUM: "border-[#D97706] text-[#D97706]",
  LOW: "border-[#DC2626] text-[#DC2626]",
};

export function ConfidencePill({
  confidence,
  label,
}: {
  confidence: Confidence | null | undefined;
  label?: string;
}) {
  if (!confidence || confidence === "N/A") return null;
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        CONFIDENCE_STYLES[confidence] ?? "border-edge text-ink-muted"
      }`}
    >
      {label ? `${label}: ` : ""}
      {confidence}
    </span>
  );
}

const LIFECYCLE_STYLES: Record<string, string> = {
  NEW: "bg-[#2563EB]/10 text-[#2563EB]",
  "EOL WATCH": "bg-[#D97706]/10 text-[#D97706]",
  RETIRED: "bg-[#DC2626]/10 text-[#DC2626]",
};

export function LifecycleBadge({ lifecycle }: { lifecycle: Lifecycle | null | undefined }) {
  if (!lifecycle || lifecycle === "UNKNOWN") return null;
  return (
    <span
      className={`inline-block rounded px-1.5 py-0.5 text-[11px] font-semibold ${
        LIFECYCLE_STYLES[lifecycle] ?? "bg-surface-2 text-ink-muted"
      }`}
    >
      {lifecycle}
    </span>
  );
}
