"use client";

import { useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, Brush,
} from "recharts";
import ChartCard from "@/components/ChartCard";
import PeriodSelector from "@/components/PeriodSelector";
import GranularitySelector, { Granularity, defaultGranularity } from "@/components/GranularitySelector";
import { LoadingState, ErrorState } from "@/components/LoadingState";
import { useAnalytics } from "@/hooks/useAnalytics";
import { chartTooltipStyle, chartTick, chartTickStrong, chartBrushStyle, renderPieLabel, fillTimeSeries } from "@/lib/chartConfig";

interface SubsData {
  by_status: { status: string; count: number }[];
  by_plan: { plan__name: string; count: number }[];
  revenue_trend: { date: string; revenue: number }[];
  active_count: number;
}

const COLORS = ["#EC4899", "#A855F7", "#6366F1", "#14B8A6", "#F59E0B"];

function formatTick(dateStr: string, granularity: Granularity): string {
  const d = new Date(dateStr);
  if (granularity === "hour") return d.toLocaleString("en", { month: "short", day: "numeric", hour: "numeric" });
  return d.toLocaleDateString("en", { month: "short", day: "numeric" });
}

export default function SubscriptionsPage() {
  const [period, setPeriod] = useState("30d");
  const [granularity, setGranularity] = useState<Granularity>(defaultGranularity("30d"));
  const { data, loading, error } = useAnalytics<SubsData>("subscriptions", period, granularity);

  const revTrend = useMemo(() => {
    if (!data) return [] as { date: string; revenue: number }[];
    const raw = data.revenue_trend.map((d) => ({ date: d.date, revenue: Number(d.revenue) }));
    return fillTimeSeries(raw, period, granularity, ["revenue"], (iso) => formatTick(iso, granularity)) as unknown as { date: string; revenue: number }[];
  }, [data, granularity, period]);

  const onPeriodChange = (p: string) => {
    setPeriod(p);
    setGranularity(defaultGranularity(p));
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const statusData = data.by_status.map((d) => ({ name: d.status, value: d.count }));
  const statusTotal = statusData.reduce((s, d) => s + d.value, 0);
  const planData = data.by_plan.map((d) => ({ name: d.plan__name, value: d.count }));
  const planTotal = planData.reduce((s, d) => s + d.value, 0);
  const revTotal = revTrend.reduce((s, d) => s + d.revenue, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-fg">Subscriptions</h1>
          <p className="text-sm text-fg-muted mt-0.5">{data.active_count} active subscriptions</p>
        </div>
        <div className="flex items-center gap-2">
          <GranularitySelector value={granularity} onChange={setGranularity} period={period} />
          <PeriodSelector value={period} onChange={onPeriodChange} />
        </div>
      </div>

      <ChartCard title="Revenue Trend" total={`$${revTotal.toFixed(2)}`} totalLabel="earned">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={revTrend}>
            <defs>
              <linearGradient id="revg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#14B8A6" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#14B8A6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
            <YAxis tick={chartTick} axisLine={false} tickLine={false} width={40} />
            <Tooltip {...chartTooltipStyle} />
            <Area type="monotone" dataKey="revenue" stroke="#14B8A6" fill="url(#revg)" strokeWidth={2} />
            <Brush dataKey="date" {...chartBrushStyle} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="By Status" total={statusTotal}>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={statusData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={renderPieLabel} labelLine={false}>
                {statusData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...chartTooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="By Plan" total={planTotal}>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={planData}>
              <XAxis dataKey="name" tick={chartTickStrong} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={40}>
                {planData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
