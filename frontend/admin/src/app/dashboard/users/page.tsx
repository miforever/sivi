"use client";

import { useMemo, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, Brush,
} from "recharts";
import ChartCard from "@/components/ChartCard";
import PeriodSelector from "@/components/PeriodSelector";
import GranularitySelector, { Granularity, defaultGranularity } from "@/components/GranularitySelector";
import { LoadingState, ErrorState } from "@/components/LoadingState";
import { useAnalytics } from "@/hooks/useAnalytics";
import { chartTooltipStyle, chartTick, chartTickStrong, chartBrushStyle, renderPieLabel, fillTimeSeries, timeSlots, slotKey } from "@/lib/chartConfig";

interface UsersData {
  growth: { date: string; count: number }[];
  growth_by_language: { date: string; language: string; count: number }[];
  language_distribution: { language: string; count: number }[];
  total: number;
}

const COLORS = ["#EC4899", "#A855F7", "#6366F1", "#14B8A6", "#F59E0B", "#EF4444"];

type Row = { date: string; _ts: number; [key: string]: string | number };

function formatTick(dateStr: string, granularity: Granularity): string {
  const d = new Date(dateStr);
  if (granularity === "hour") return d.toLocaleString("en", { month: "short", day: "numeric", hour: "numeric" });
  return d.toLocaleDateString("en", { month: "short", day: "numeric" });
}

export default function UsersPage() {
  const [period, setPeriod] = useState("30d");
  const [granularity, setGranularity] = useState<Granularity>(defaultGranularity("30d"));
  const [splitByLang, setSplitByLang] = useState(false);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const { data, loading, error } = useAnalytics<UsersData>("users", period, granularity);

  const fmt = (iso: string) => formatTick(iso, granularity);

  const growth = useMemo(() => {
    if (!data) return [] as { date: string; users: number }[];
    const raw = data.growth.map((d) => ({ date: d.date, users: d.count }));
    return fillTimeSeries(raw, period, granularity, ["users"], fmt) as unknown as { date: string; users: number }[];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, granularity, period]);

  const { langs, growthByLang } = useMemo(() => {
    if (!data) return { langs: [] as string[], growthByLang: [] as Row[] };
    const langSet = new Set<string>();
    const bySlot = new Map<string, Row>();

    // Accumulate data rows
    data.growth_by_language.forEach((d) => {
      const lang = d.language || "unk";
      langSet.add(lang);
      const slot = timeSlots(period, granularity).find(
        (s) => slotKey(s, granularity) === slotKey(new Date(d.date), granularity),
      );
      const label = fmt(slot ? slot.toISOString() : d.date);
      const row = bySlot.get(label) || { date: label, _ts: slot ? slot.getTime() : new Date(d.date).getTime() };
      row[lang] = ((row[lang] as number) || 0) + d.count;
      bySlot.set(label, row);
    });

    const langList = Array.from(langSet);

    // Fill all slots (missing slots get 0 for every language)
    const allRows = timeSlots(period, granularity).map((slot) => {
      const label = fmt(slot.toISOString());
      const existing = bySlot.get(label);
      if (existing) return existing;
      const empty: Row = { date: label, _ts: slot.getTime() };
      for (const l of langList) empty[l] = 0;
      return empty;
    });

    return { langs: langList, growthByLang: allRows };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, granularity, period]);

  const toggleSeries = (key: string) => {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const onPeriodChange = (p: string) => {
    setPeriod(p);
    setGranularity(defaultGranularity(p));
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const langData = data.language_distribution.map((d) => ({
    name: d.language || "Unknown",
    value: d.count,
  }));
  const langTotal = langData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-fg">Users</h1>
          <p className="text-sm text-fg-muted mt-0.5">{data.total.toLocaleString()} total users</p>
        </div>
        <div className="flex items-center gap-2">
          <GranularitySelector value={granularity} onChange={setGranularity} period={period} />
          <PeriodSelector value={period} onChange={onPeriodChange} />
        </div>
      </div>

      <ChartCard
        title="User Registrations"
        total={splitByLang ? undefined : growth.reduce((s, d) => s + d.users, 0)}
        totalLabel="new"
        action={
          <div className="flex gap-1 p-0.5 rounded-md bg-overlay border border-edge-strong text-xs">
            <button
              onClick={() => setSplitByLang(false)}
              className={`px-2 py-1 rounded ${!splitByLang ? "bg-brand-500 text-white" : "text-fg-muted"}`}
            >
              Total
            </button>
            <button
              onClick={() => setSplitByLang(true)}
              className={`px-2 py-1 rounded ${splitByLang ? "bg-brand-500 text-white" : "text-fg-muted"}`}
            >
              By language
            </button>
          </div>
        }
      >
        <ResponsiveContainer width="100%" height={260}>
          {splitByLang ? (
            <AreaChart data={growthByLang}>
              <defs>
                {langs.map((l, i) => (
                  <linearGradient key={l} id={`lg_${l}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Legend onClick={(e) => toggleSeries(`${e.dataKey}`)} wrapperStyle={{ fontSize: 12, cursor: "pointer" }} />
              {langs.map((l, i) => (
                <Area
                  key={l}
                  type="monotone"
                  dataKey={l}
                  stackId="1"
                  stroke={COLORS[i % COLORS.length]}
                  fill={`url(#lg_${l})`}
                  strokeWidth={2}
                  hide={hidden.has(l)}
                />
              ))}
              <Brush dataKey="date" {...chartBrushStyle} />
            </AreaChart>
          ) : (
            <AreaChart data={growth}>
              <defs>
                <linearGradient id="ug" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#EC4899" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#EC4899" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Area type="monotone" dataKey="users" stroke="#EC4899" fill="url(#ug)" strokeWidth={2} />
              <Brush dataKey="date" {...chartBrushStyle} />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Language Distribution" total={langTotal}>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={langData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={renderPieLabel} labelLine={false}>
                {langData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...chartTooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Users by Language" total={langTotal}>
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
