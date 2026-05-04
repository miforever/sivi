"use client";

import { useMemo, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Brush,
} from "recharts";
import ChartCard from "@/components/ChartCard";
import PeriodSelector from "@/components/PeriodSelector";
import GranularitySelector, { Granularity, defaultGranularity } from "@/components/GranularitySelector";
import { LoadingState, ErrorState } from "@/components/LoadingState";
import { useAnalytics } from "@/hooks/useAnalytics";
import { chartTooltipStyle, chartTick, chartTickStrong, chartBrushStyle, renderPieLabel, fillTimeSeries } from "@/lib/chartConfig";

interface ResumesData {
  by_origin: { origin: string; count: number }[];
  by_language: { language: string; count: number }[];
  trend: { date: string; count: number }[];
  total: number;
}

const COLORS = ["#A855F7", "#EC4899", "#6366F1", "#14B8A6", "#F59E0B"];

function formatTick(dateStr: string, granularity: Granularity): string {
  const d = new Date(dateStr);
  if (granularity === "hour") return d.toLocaleString("en", { month: "short", day: "numeric", hour: "numeric" });
  return d.toLocaleDateString("en", { month: "short", day: "numeric" });
}

export default function ResumesPage() {
  const [period, setPeriod] = useState("30d");
  const [granularity, setGranularity] = useState<Granularity>(defaultGranularity("30d"));
  const { data, loading, error } = useAnalytics<ResumesData>("resumes", period, granularity);

  const trend = useMemo(() => {
    if (!data) return [] as { date: string; resumes: number }[];
    const raw = data.trend.map((d) => ({ date: d.date, resumes: d.count }));
    return fillTimeSeries(raw, period, granularity, ["resumes"], (iso) => formatTick(iso, granularity)) as unknown as { date: string; resumes: number }[];
  }, [data, granularity, period]);

  const onPeriodChange = (p: string) => {
    setPeriod(p);
    setGranularity(defaultGranularity(p));
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const originData = data.by_origin.map((d) => ({
    name: d.origin || "Unknown",
    value: d.count,
  }));
  const originTotal = originData.reduce((s, d) => s + d.value, 0);

  const langData = data.by_language.map((d) => ({
    name: d.language || "Unknown",
    value: d.count,
  }));
  const langTotal = langData.reduce((s, d) => s + d.value, 0);
  const trendTotal = trend.reduce((s, d) => s + d.resumes, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-fg">Resumes</h1>
          <p className="text-sm text-fg-muted mt-0.5">{data.total.toLocaleString()} total resumes</p>
        </div>
        <div className="flex items-center gap-2">
          <GranularitySelector value={granularity} onChange={setGranularity} period={period} />
          <PeriodSelector value={period} onChange={onPeriodChange} />
        </div>
      </div>

      <ChartCard title="Creation Trend" total={trendTotal} totalLabel="created">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={trend}>
            <defs>
              <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#A855F7" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#A855F7" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
            <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
            <Tooltip {...chartTooltipStyle} />
            <Area type="monotone" dataKey="resumes" stroke="#A855F7" fill="url(#rg)" strokeWidth={2} />
            <Brush dataKey="date" {...chartBrushStyle} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="By Origin" total={originTotal}>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={originData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={renderPieLabel} labelLine={false}>
                {originData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...chartTooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="By Language" total={langTotal}>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={langData} layout="vertical">
              <XAxis type="number" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={chartTickStrong} axisLine={false} tickLine={false} width={70} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                {langData.map((_, i) => (
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
