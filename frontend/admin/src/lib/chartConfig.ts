import type { Granularity } from "@/components/GranularitySelector";

// ─── Time-series fill helpers ────────────────────────────────────────────────

function slotKey(d: Date, g: Granularity): string {
  return g === "hour"
    ? `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}-${d.getHours()}`
    : `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

function periodMs(period: string): number {
  const map: Record<string, number> = {
    "1d": 86_400_000,
    "7d": 7 * 86_400_000,
    "30d": 30 * 86_400_000,
    "90d": 90 * 86_400_000,
    "1y": 365 * 86_400_000,
  };
  return map[period] ?? 30 * 86_400_000;
}

/** All Date objects for every slot in [now-period, now], aligned to slot boundaries. */
export function timeSlots(period: string, granularity: Granularity): Date[] {
  const now = new Date();
  const start = new Date(now.getTime() - periodMs(period));
  if (granularity === "hour") start.setMinutes(0, 0, 0);
  else start.setHours(0, 0, 0, 0);

  const stepMs = granularity === "hour" ? 3_600_000 : 86_400_000;
  const slots: Date[] = [];
  const cursor = new Date(start);
  while (cursor.getTime() <= now.getTime()) {
    slots.push(new Date(cursor));
    cursor.setTime(cursor.getTime() + stepMs);
  }
  return slots;
}

/**
 * Fill rawData against every time slot in [now-period, now].
 * Rows with the same slot are summed; missing slots get 0 for all numericKeys.
 * formatLabel converts an ISO date string to the chart label (same fn used on data rows).
 */
export function fillTimeSeries(
  rawData: { date: string; [key: string]: unknown }[],
  period: string,
  granularity: Granularity,
  numericKeys: string[],
  formatLabel: (isoDate: string) => string,
): { date: string; [key: string]: unknown }[] {
  const lookup = new Map<string, Record<string, number>>();
  for (const row of rawData) {
    const key = slotKey(new Date(row.date), granularity);
    if (!lookup.has(key)) lookup.set(key, Object.fromEntries(numericKeys.map((k) => [k, 0])));
    const bucket = lookup.get(key)!;
    for (const k of numericKeys) bucket[k] += Number(row[k]) || 0;
  }

  const zero = Object.fromEntries(numericKeys.map((k) => [k, 0]));
  return timeSlots(period, granularity).map((slot) => ({
    date: formatLabel(slot.toISOString()),
    ...(lookup.get(slotKey(slot, granularity)) ?? zero),
  }));
}

/** Slot key accessor — useful when pages need to fill pivoted / multi-series data. */
export { slotKey };

// ─── Chart style config ───────────────────────────────────────────────────────

export const chartTooltipStyle = {
  contentStyle: {
    background: "var(--chart-tooltip-bg)",
    border: "1px solid var(--chart-tooltip-border)",
    borderRadius: "8px",
    fontSize: "12px",
    color: "var(--chart-tooltip-color)",
  },
  labelStyle: { color: "var(--chart-tooltip-color)", fontWeight: 500 },
  itemStyle: { color: "var(--chart-tooltip-color)" },
};

export const chartTick = {
  fill: "var(--chart-text-strong)",
  fontSize: 12,
};

export const chartTickStrong = {
  fill: "var(--chart-text-strong)",
  fontSize: 12,
};

export const chartLabelStyle = {
  fill: "var(--chart-text-strong)",
  fontSize: 11,
};

export const chartBrushStyle = {
  stroke: "var(--chart-text-strong)",
  fill: "transparent",
  travellerWidth: 8,
  height: 24,
};

// Custom pie label renderer — uses theme-aware fill (fixes dark-on-dark default).
// Place labels just outside the slice, with a small polyline.
interface PieLabelArgs {
  cx: number;
  cy: number;
  midAngle?: number;
  outerRadius: number;
  percent?: number;
  name?: string;
}

import { createElement } from "react";

export function renderPieLabel(props: PieLabelArgs) {
  const { cx, cy, midAngle = 0, outerRadius, percent = 0, name = "" } = props;
  const RAD = Math.PI / 180;
  const r = outerRadius + 12;
  const x = cx + r * Math.cos(-midAngle * RAD);
  const y = cy + r * Math.sin(-midAngle * RAD);
  const anchor = x > cx ? "start" : "end";
  return createElement(
    "text",
    {
      x,
      y,
      textAnchor: anchor,
      dominantBaseline: "central",
      fill: "var(--chart-text-strong)",
      fontSize: 11,
    },
    `${name} ${(percent * 100).toFixed(0)}%`,
  );
}
