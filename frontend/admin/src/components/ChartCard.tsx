"use client";

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  total?: number | string;
  totalLabel?: string;
  action?: React.ReactNode;
}

export default function ChartCard({
  title,
  children,
  className = "",
  total,
  totalLabel,
  action,
}: ChartCardProps) {
  return (
    <div className={`p-5 rounded-xl border border-edge bg-surface-card/60 backdrop-blur-sm ${className}`}>
      <div className="flex items-start justify-between mb-4 gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-fg-secondary">{title}</h3>
          {total !== undefined && (
            <p className="text-xs text-[var(--chart-text-strong)] mt-0.5">
              {typeof total === "number" ? total.toLocaleString() : total}
              {totalLabel ? ` ${totalLabel}` : " total"}
            </p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children}
    </div>
  );
}
