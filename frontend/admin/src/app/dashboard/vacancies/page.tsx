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
import { chartTooltipStyle, chartTick, chartTickStrong, chartBrushStyle, renderPieLabel } from "@/lib/chartConfig";

interface VacanciesData {
  trend: { date: string; count: number }[];
  by_source: { source: string; count: number }[];
  by_channel: { source_channel: string; count: number }[];
  by_employment_type: { employment_type: string; count: number }[];
  by_region: { region: string; name: string; count: number }[];
  avg_salary: { min: number; max: number; currency?: string };
  source_names?: Record<string, string>;
  total: number;
}

const COLORS = ["#6366F1", "#EC4899", "#A855F7", "#14B8A6", "#F59E0B", "#EF4444", "#10B981", "#8B5CF6"];

function formatSalary(value: number, currency: string) {
  if (currency === "UZS") {
    return `${Math.round(value).toLocaleString()} UZS`;
  }
  return `$${Math.round(value).toLocaleString()}`;
}

function formatTick(dateStr: string, granularity: Granularity): string {
  const d = new Date(dateStr);
  if (granularity === "hour") return d.toLocaleString("en", { month: "short", day: "numeric", hour: "numeric" });
  return d.toLocaleDateString("en", { month: "short", day: "numeric" });
}

export default function VacanciesPage() {
  const [period, setPeriod] = useState("30d");
  const [granularity, setGranularity] = useState<Granularity>(defaultGranularity("30d"));
  const { data, loading, error } = useAnalytics<VacanciesData>("vacancies", period, granularity);

  const trend = useMemo(() => {
    if (!data?.trend) return [];
    return data.trend.map((d) => ({
      date: formatTick(d.date, granularity),
      vacancies: d.count,
    }));
  }, [data, granularity]);

  const onPeriodChange = (p: string) => {
    setPeriod(p);
    setGranularity(defaultGranularity(p));
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const currency = data.avg_salary.currency || "USD";
  const names = data.source_names || {};

  // Build pie chart from by_channel with human-readable names, top 8 + "Other"
  const allChannels = data.by_channel.map((d) => ({
    name: names[d.source_channel] || d.source_channel,
    value: d.count,
  }));
  const topChannels = allChannels.slice(0, 8);
  const otherCount = allChannels.slice(8).reduce((s, d) => s + d.value, 0);
  const sourceData = otherCount > 0
    ? [...topChannels, { name: "Other", value: otherCount }]
    : topChannels;

  const typeData = data.by_employment_type.map((d) => ({ name: d.employment_type || "Unspecified", value: d.count }));
  const typeTotal = typeData.reduce((s, d) => s + d.value, 0);
  const sourceTotal = sourceData.reduce((s, d) => s + d.value, 0);
  const trendTotal = trend.reduce((s, d) => s + d.vacancies, 0);

  // Top channels bar chart uses the same human-readable names
  const channelData = data.by_channel.slice(0, 8).map((d) => ({
    name: names[d.source_channel] || d.source_channel,
    value: d.count,
  }));
  const channelTotal = channelData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-fg">Vacancies</h1>
          <p className="text-sm text-fg-muted mt-0.5">{data.total.toLocaleString()} total vacancies indexed</p>
        </div>
        <div className="flex items-center gap-2">
          <GranularitySelector value={granularity} onChange={setGranularity} period={period} />
          <PeriodSelector value={period} onChange={onPeriodChange} />
        </div>
      </div>

      {/* Vacancies Over Time */}
      <ChartCard title="Vacancies Over Time" total={trendTotal} totalLabel="indexed">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={trend}>
            <defs>
              <linearGradient id="vacGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366F1" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
            <YAxis tick={chartTick} axisLine={false} tickLine={false} width={40} />
            <Tooltip {...chartTooltipStyle} />
            <Area type="monotone" dataKey="vacancies" stroke="#6366F1" fill="url(#vacGrad)" strokeWidth={2} />
            <Brush dataKey="date" {...chartBrushStyle} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Salary Info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-5 rounded-xl border border-edge bg-surface-card/60">
          <p className="text-sm text-fg-muted">Avg Min Salary</p>
          <p className="text-2xl font-bold text-fg mt-1">{formatSalary(data.avg_salary.min, currency)}</p>
        </div>
        <div className="p-5 rounded-xl border border-edge bg-surface-card/60">
          <p className="text-sm text-fg-muted">Avg Max Salary</p>
          <p className="text-2xl font-bold text-fg mt-1">{formatSalary(data.avg_salary.max, currency)}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="By Source" total={sourceTotal}>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={sourceData} cx="50%" cy="50%" outerRadius={75} dataKey="value" label={renderPieLabel} labelLine={false}>
                {sourceData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...chartTooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="By Employment Type" total={typeTotal}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={typeData}>
              <XAxis dataKey="name" tick={{ ...chartTickStrong, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={30}>
                {typeData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {channelData.length > 0 && (
        <ChartCard title="Top Channels" total={channelTotal}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={channelData} layout="vertical">
              <XAxis type="number" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ ...chartTickStrong, fontSize: 11 }} axisLine={false} tickLine={false} width={140} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={18}>
                {channelData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {data.by_region && data.by_region.length > 0 && (
        <ChartCard title="By Region" total={data.by_region.reduce((s, d) => s + d.count, 0)}>
          <ResponsiveContainer width="100%" height={Math.max(280, data.by_region.length * 32)}>
            <BarChart data={data.by_region.map((d) => ({ name: d.name, value: d.count }))} layout="vertical">
              <XAxis type="number" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ ...chartTickStrong, fontSize: 11 }} axisLine={false} tickLine={false} width={140} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={18}>
                {data.by_region.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}
    </div>
  );
}
