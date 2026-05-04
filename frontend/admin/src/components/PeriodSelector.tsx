"use client";

const periods = [
  { label: "1D", value: "1d" },
  { label: "7D", value: "7d" },
  { label: "30D", value: "30d" },
  { label: "90D", value: "90d" },
  { label: "1Y", value: "1y" },
];

interface PeriodSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  return (
    <div className="flex gap-1 p-1 rounded-lg bg-overlay border border-edge-strong">
      {periods.map((p) => (
        <button
          key={p.value}
          onClick={() => onChange(p.value)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            value === p.value
              ? "bg-brand-500 text-white shadow-sm"
              : "text-fg-muted hover:text-fg-secondary"
          }`}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
