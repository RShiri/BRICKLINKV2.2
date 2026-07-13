"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PricePoint } from "@/lib/types";

export function PriceHistoryChart({ history }: { history: PricePoint[] }) {
  const data = history.map((p) => ({
    date: new Date(p.scraped_at).toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
    }),
    New: p.price_new && p.price_new > 0 ? p.price_new : null,
    Used: p.price_used && p.price_used > 0 ? p.price_used : null,
  }));

  if (data.length < 2) {
    return (
      <p className="rounded border border-dashed border-edge p-6 text-center text-[13px] text-ink-muted">
        Not enough price history yet — re-analyze this item over time to build a chart.
      </p>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--text-muted)" }}
            tickFormatter={(v: number) => `₪${v}`}
            width={56}
          />
          <Tooltip
            formatter={(value) => [`₪${Number(value).toFixed(2)}`]}
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              fontSize: 12,
              color: "var(--text)",
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="New" stroke="#0057A6" dot={false} strokeWidth={2} connectNulls />
          <Line type="monotone" dataKey="Used" stroke="#D97706" dot={false} strokeWidth={2} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
