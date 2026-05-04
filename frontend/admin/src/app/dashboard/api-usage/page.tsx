"use client";

import { useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, AreaChart, Area, Brush,
} from "recharts";
import ChartCard from "@/components/ChartCard";
import PeriodSelector from "@/components/PeriodSelector";
import GranularitySelector, { Granularity, defaultGranularity } from "@/components/GranularitySelector";
import { LoadingState, ErrorState } from "@/components/LoadingState";
import { useAnalytics } from "@/hooks/useAnalytics";
import { chartTooltipStyle, chartTick, chartBrushStyle, timeSlots, slotKey } from "@/lib/chartConfig";

type TrendRow = { date: string; _ts: number; [key: string]: string | number };

interface ApiData {
  by_provider: {
    provider: string;
    count: number;
    total_tokens: number;
    total_cost: number;
    avg_response_ms: number;
    error_count: number;
  }[];
  trend: { date: string; provider: string; count: number; tokens: number; cost: number }[];
  total_calls: number;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: "#10B981",
  fireworks: "#F59E0B",
  anthropic: "#EC4899",
  google: "#6366F1",
};

function formatTick(dateStr: string, granularity: Granularity): string {
  const d = new Date(dateStr);
  if (granularity === "hour") {
    return d.toLocaleString("en", { month: "short", day: "numeric", hour: "numeric" });
  }
  return d.toLocaleDateString("en", { month: "short", day: "numeric" });
}

export default function ApiUsagePage() {
  const [period, setPeriod] = useState("30d");
  const [granularity, setGranularity] = useState<Granularity>(defaultGranularity("30d"));
  const { data, loading, error } = useAnalytics<ApiData>("api-usage", period, granularity);

  // Pivot trend rows into { date, openai_calls, fireworks_calls, ... } shape.
  const { providers, trendData } = useMemo(() => {
    if (!data) return { providers: [] as string[], trendData: [] as TrendRow[] };
    const providerSet = new Set<string>();
    const bySlot = new Map<string, TrendRow>();
    const slots = timeSlots(period, granularity);
    const fmt = (iso: string) => formatTick(iso, granularity);

    data.trend.forEach((d) => {
      const p = d.provider.toLowerCase();
      providerSet.add(p);
      const slot = slots.find((s) => slotKey(s, granularity) === slotKey(new Date(d.date), granularity));
      const label = fmt(slot ? slot.toISOString() : d.date);
      const existing = bySlot.get(label) || { date: label, _ts: slot ? slot.getTime() : new Date(d.date).getTime() };
      existing[`${p}_calls`] = ((existing[`${p}_calls`] as number) || 0) + d.count;
      existing[`${p}_cost`] = ((existing[`${p}_cost`] as number) || 0) + Number(d.cost || 0);
      bySlot.set(label, existing);
    });

    const providerList = Array.from(providerSet);

    // Fill all slots so every time point appears even with 0 data
    const rows = slots.map((slot) => {
      const label = fmt(slot.toISOString());
      const existing = bySlot.get(label);
      if (existing) return existing;
      const empty: TrendRow = { date: label, _ts: slot.getTime() };
      for (const p of providerList) {
        empty[`${p}_calls`] = 0;
        empty[`${p}_cost`] = 0;
      }
      return empty;
    });

    return { providers: providerList, trendData: rows };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, granularity, period]);

  const onPeriodChange = (p: string) => {
    setPeriod(p);
    setGranularity(defaultGranularity(p));
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const totalCost = data.by_provider.reduce((s, p) => s + Number(p.total_cost), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-fg">API Usage</h1>
          <p className="text-sm text-fg-muted mt-0.5">{data.total_calls.toLocaleString()} calls in period</p>
        </div>
        <div className="flex items-center gap-2">
          <GranularitySelector value={granularity} onChange={setGranularity} period={period} />
          <PeriodSelector value={period} onChange={onPeriodChange} />
        </div>
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.by_provider.map((p) => (
          <div key={p.provider} className="p-5 rounded-xl border border-edge bg-surface-card/60">
            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: PROVIDER_COLORS[p.provider.toLowerCase()] || "#888" }}
              />
              <h3 className="text-sm font-medium text-fg capitalize">{p.provider}</h3>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-fg-muted">Calls</span>
                <span className="text-fg font-medium">{p.count.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-fg-muted">Tokens</span>
                <span className="text-fg font-medium">{(p.total_tokens || 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-fg-muted">Cost</span>
                <span className="text-fg font-medium">${Number(p.total_cost).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-fg-muted">Avg Response</span>
                <span className="text-fg font-medium">{Math.round(p.avg_response_ms)}ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-fg-muted">Errors</span>
                <span className={`font-medium ${p.error_count > 0 ? "text-red-400" : "text-emerald-400"}`}>
                  {p.error_count}
                </span>
              </div>
            </div>
          </div>
        ))}
        <div className="p-5 rounded-xl border border-edge bg-surface-card/60 flex flex-col justify-center">
          <p className="text-sm text-fg-muted">Total Cost (Period)</p>
          <p className="text-3xl font-bold text-fg mt-1">${totalCost.toFixed(2)}</p>
        </div>
      </div>

      {/* Calls Over Time — 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {providers.map((provider) => {
          const color = PROVIDER_COLORS[provider] || "#6366F1";
          const name = provider.charAt(0).toUpperCase() + provider.slice(1);
          const gradId = `grad_calls_${provider}`;
          const providerTrend = trendData.map((row) => ({
            date: row.date,
            calls: (row[`${provider}_calls`] as number) || 0,
          }));
          const providerCalls = providerTrend.reduce((s, d) => s + d.calls, 0);

          return (
            <ChartCard key={provider} title={`${name} — Calls Over Time`} total={providerCalls} totalLabel="calls">
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={providerTrend}>
                  <defs>
                    <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={color} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={color} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
                  <YAxis tick={chartTick} axisLine={false} tickLine={false} width={40} />
                  <Tooltip {...chartTooltipStyle} />
                  <Area
                    type="monotone"
                    dataKey="calls"
                    name={name}
                    stroke={color}
                    fill={`url(#${gradId})`}
                    strokeWidth={2}
                  />
                  <Brush dataKey="date" {...chartBrushStyle} />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          );
        })}
      </div>

      {/* Cost Over Time — 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {providers.map((provider) => {
          const color = PROVIDER_COLORS[provider] || "#6366F1";
          const name = provider.charAt(0).toUpperCase() + provider.slice(1);
          const providerTrend = trendData.map((row) => ({
            date: row.date,
            cost: (row[`${provider}_cost`] as number) || 0,
          }));
          const providerCost = providerTrend.reduce((s, d) => s + d.cost, 0);

          return (
            <ChartCard key={provider} title={`${name} — Cost Over Time`} total={`$${providerCost.toFixed(2)}`} totalLabel="spent">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={providerTrend}>
                  <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
                  <YAxis tick={chartTick} axisLine={false} tickLine={false} width={50} tickFormatter={(v) => `$${v}`} />
                  <Tooltip {...chartTooltipStyle} formatter={(value) => `$${Number(value).toFixed(2)}`} />
                  <Bar dataKey="cost" name={name} fill={color} radius={[4, 4, 0, 0]} />
                  <Brush dataKey="date" {...chartBrushStyle} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          );
        })}
      </div>
    </div>
  );
}
