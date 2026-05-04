"use client";

import { useAnalytics } from "@/hooks/useAnalytics";
import { LoadingState, ErrorState } from "@/components/LoadingState";

interface HealthCheck {
  status: string;
  message?: string;
  workers?: number;
}

interface ResourceUsage {
  total_gb: number;
  used_gb: number;
  percent: number;
}

interface Resources {
  cpu_percent: number;
  memory: ResourceUsage;
  disk: ResourceUsage;
}

interface HealthData {
  status: string;
  checks: Record<string, HealthCheck>;
  resources: Resources | null;
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "ok" ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]" :
    status === "error" ? "bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.6)]" :
    status === "warning" ? "bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.6)]" :
    "bg-zinc-500";
  return <div className={`w-2 h-2 rounded-full ${color}`} />;
}

function RingGauge({ percent, label, detail }: { percent: number; label: string; detail: string }) {
  const radius = 40;
  const stroke = 6;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;
  const color =
    percent >= 90 ? "stroke-red-400" :
    percent >= 70 ? "stroke-amber-400" :
    "stroke-emerald-400";

  return (
    <div className="flex flex-col items-center gap-2 p-5 rounded-2xl bg-overlay/50 border border-edge">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 96 96">
          <circle cx="48" cy="48" r={radius} fill="none" stroke="currentColor" strokeWidth={stroke} className="text-edge" />
          <circle cx="48" cy="48" r={radius} fill="none" strokeWidth={stroke} strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} className={`${color} transition-all duration-700`} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-semibold text-fg tabular-nums">{Math.round(percent)}%</span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-fg">{label}</p>
        <p className="text-xs text-fg-muted">{detail}</p>
      </div>
    </div>
  );
}

export default function HealthPage() {
  const { data, loading, error, refetch } = useAnalytics<HealthData>("health");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const overallOk = data.status === "healthy";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-2.5 h-2.5 rounded-full ${overallOk ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" : "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]"}`} />
          <div>
            <h1 className="text-xl font-bold text-fg">System</h1>
            <p className="text-xs text-fg-muted mt-0.5">
              {overallOk ? "All systems operational" : "Some systems degraded"}
            </p>
          </div>
        </div>
        <button
          onClick={refetch}
          className="px-3 py-1.5 rounded-lg bg-overlay border border-edge text-xs text-fg-secondary hover:text-fg hover:bg-overlay-hover transition-all"
        >
          Refresh
        </button>
      </div>

      {/* Services — compact inline row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {Object.entries(data.checks).map(([name, check]) => (
          <div key={name} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-overlay/50 border border-edge">
            <StatusDot status={check.status} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-fg capitalize">{name}</p>
              <p className="text-xs text-fg-muted truncate">
                {check.message
                  ? check.message
                  : check.workers !== undefined
                    ? `${check.workers} worker${check.workers !== 1 ? "s" : ""}`
                    : check.status === "ok" ? "Operational" : check.status}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Resources */}
      {data.resources && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-fg-secondary uppercase tracking-wider">Resources</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <RingGauge
              percent={data.resources.cpu_percent}
              label="CPU"
              detail={`${data.resources.cpu_percent.toFixed(1)}% utilized`}
            />
            <RingGauge
              percent={data.resources.memory.percent}
              label="Memory"
              detail={`${data.resources.memory.used_gb} / ${data.resources.memory.total_gb} GB`}
            />
            <RingGauge
              percent={data.resources.disk.percent}
              label="Disk"
              detail={`${data.resources.disk.used_gb} / ${data.resources.disk.total_gb} GB`}
            />
          </div>
        </div>
      )}
    </div>
  );
}
