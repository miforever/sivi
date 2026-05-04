"use client";

export type Granularity = "hour" | "day";

const ALL_OPTIONS: { label: string; value: Granularity }[] = [
  { label: "H", value: "hour" },
  { label: "D", value: "day" },
];

// Which granularities make sense for each period.
const VALID_FOR_PERIOD: Record<string, Granularity[]> = {
  "1d": ["hour"],
  "7d": ["hour", "day"],
  "30d": ["hour", "day"],
  "90d": ["day"],
  "1y": ["day"],
};

export function defaultGranularity(period: string): Granularity {
  return period === "1d" ? "hour" : "day";
}

interface Props {
  value: Granularity;
  onChange: (value: Granularity) => void;
  period: string;
}

export default function GranularitySelector({ value, onChange, period }: Props) {
  const valid = new Set(VALID_FOR_PERIOD[period] || ["day"]);

  return (
    <div className="flex gap-1 p-1 rounded-lg bg-overlay border border-edge-strong">
      {ALL_OPTIONS.map((opt) => {
        const enabled = valid.has(opt.value);
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            disabled={!enabled}
            onClick={() => onChange(opt.value)}
            title={opt.value}
            className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
              active
                ? "bg-brand-500 text-white shadow-sm"
                : enabled
                  ? "text-fg-muted hover:text-fg-secondary"
                  : "text-fg-faint opacity-40 cursor-not-allowed"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
