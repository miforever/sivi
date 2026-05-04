"use client";

interface KpiCardProps {
  title: string;
  value: string | number;
  change?: string;
  positive?: boolean;
  icon: React.ReactNode;
}

export default function KpiCard({ title, value, change, positive, icon }: KpiCardProps) {
  return (
    <div className="p-5 rounded-xl border border-edge bg-surface-card/60 backdrop-blur-sm">
      <div className="flex items-start justify-between mb-3">
        <span className="text-fg-muted text-sm">{title}</span>
        <span className="text-fg-icon">{icon}</span>
      </div>
      <div className="text-2xl font-bold text-fg">{value}</div>
      {change && (
        <p className={`text-xs mt-1 ${positive ? "text-emerald-400" : "text-red-400"}`}>
          {positive ? "+" : ""}{change} from last period
        </p>
      )}
    </div>
  );
}
