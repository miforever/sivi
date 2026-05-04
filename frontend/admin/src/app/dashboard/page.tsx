"use client";

import { useMemo, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Brush,
} from "recharts";
import KpiCard from "@/components/KpiCard";
import ChartCard from "@/components/ChartCard";
import PeriodSelector from "@/components/PeriodSelector";
import GranularitySelector, { Granularity, defaultGranularity } from "@/components/GranularitySelector";
import { LoadingState, ErrorState } from "@/components/LoadingState";
import { useAnalytics } from "@/hooks/useAnalytics";
import { chartTooltipStyle, chartTick, chartBrushStyle, fillTimeSeries } from "@/lib/chartConfig";

interface DashboardData {
  total_users: number;
  new_users_period: number;
  total_resumes: number;
  new_resumes_period: number;
  active_subscriptions: number;
  total_vacancies: number;
  revenue_period: number;
}

interface UsersData {
  growth: { date: string; count: number }[];
  total: number;
}

interface ResumesData {
  trend: { date: string; count: number }[];
  total: number;
}

interface EventsData {
  trend: { date: string; count: number }[];
  total: number;
}

interface ActiveUsersData {
  trend: { date: string; count: number }[];
  total: number;
}

function formatTick(dateStr: string, granularity: Granularity): string {
  const d = new Date(dateStr);
  if (granularity === "hour") return d.toLocaleString("en", { month: "short", day: "numeric", hour: "numeric" });
  return d.toLocaleDateString("en", { month: "short", day: "numeric" });
}

const SCROLL_EXTRA_PARAMS = { event_type: "job_feed_scroll" };

export default function OverviewPage() {
  const [period, setPeriod] = useState("30d");
  const [granularity, setGranularity] = useState<Granularity>(defaultGranularity("30d"));
  const { data: kpi, loading, error } = useAnalytics<DashboardData>("dashboard", period);
  const { data: usersData } = useAnalytics<UsersData>("users", period, granularity);
  const { data: resumesData } = useAnalytics<ResumesData>("resumes", period, granularity);
  const { data: scrollsData } = useAnalytics<EventsData>("user-events", period, granularity, SCROLL_EXTRA_PARAMS);
  const { data: activeUsersData } = useAnalytics<ActiveUsersData>("active-users", period, granularity);

  const onPeriodChange = (p: string) => {
    setPeriod(p);
    setGranularity(defaultGranularity(p));
  };

  const fmt = (iso: string) => formatTick(iso, granularity);

  const userGrowth = useMemo(() => {
    if (!usersData) return [];
    const raw = usersData.growth.map((d) => ({ date: d.date, users: d.count }));
    return fillTimeSeries(raw, period, granularity, ["users"], fmt) as unknown as { date: string; users: number }[];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usersData, granularity, period]);

  const resumeTrend = useMemo(() => {
    if (!resumesData) return [];
    const raw = resumesData.trend.map((d) => ({ date: d.date, resumes: d.count }));
    return fillTimeSeries(raw, period, granularity, ["resumes"], fmt) as unknown as { date: string; resumes: number }[];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumesData, granularity, period]);

  const scrollsTrend = useMemo(() => {
    if (!scrollsData) return [];
    const raw = scrollsData.trend.map((d) => ({ date: d.date, scrolls: d.count }));
    return fillTimeSeries(raw, period, granularity, ["scrolls"], fmt) as unknown as { date: string; scrolls: number }[];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scrollsData, granularity, period]);

  const activeUsersTrend = useMemo(() => {
    if (!activeUsersData) return [];
    const raw = activeUsersData.trend.map((d) => ({ date: d.date, users: d.count }));
    return fillTimeSeries(raw, period, granularity, ["users"], fmt) as unknown as { date: string; users: number }[];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeUsersData, granularity, period]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!kpi) return null;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-fg">Overview</h1>
          <p className="text-sm text-fg-muted mt-0.5">Platform analytics at a glance</p>
        </div>
        <div className="flex items-center gap-2">
          <GranularitySelector value={granularity} onChange={setGranularity} period={period} />
          <PeriodSelector value={period} onChange={onPeriodChange} />
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          title="Total Users"
          value={kpi.total_users.toLocaleString()}
          change={`${kpi.new_users_period} new`}
          positive
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
            </svg>
          }
        />
        <KpiCard
          title="Total Resumes"
          value={kpi.total_resumes.toLocaleString()}
          change={`${kpi.new_resumes_period} new`}
          positive
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          }
        />
        <KpiCard
          title="Active Subscriptions"
          value={kpi.active_subscriptions.toLocaleString()}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" />
            </svg>
          }
        />
        <KpiCard
          title="Revenue"
          value={`$${kpi.revenue_period.toLocaleString()}`}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
          }
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="User Growth" total={userGrowth.reduce((s, d) => s + d.users, 0)} totalLabel="new">
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={userGrowth}>
              <defs>
                <linearGradient id="userGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#EC4899" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#EC4899" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Area type="monotone" dataKey="users" stroke="#EC4899" fill="url(#userGrad)" strokeWidth={2} />
              <Brush dataKey="date" {...chartBrushStyle} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Resume Trend" total={resumeTrend.reduce((s, d) => s + d.resumes, 0)} totalLabel="created">
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={resumeTrend}>
              <defs>
                <linearGradient id="resumeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#A855F7" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#A855F7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Area type="monotone" dataKey="resumes" stroke="#A855F7" fill="url(#resumeGrad)" strokeWidth={2} />
              <Brush dataKey="date" {...chartBrushStyle} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Active Users + Resume Scrolls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Daily Active Users" total={activeUsersData?.total ?? 0} totalLabel="unique users">
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={activeUsersTrend}>
              <defs>
                <linearGradient id="activeUsersGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#F59E0B" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Area type="monotone" dataKey="users" stroke="#F59E0B" fill="url(#activeUsersGrad)" strokeWidth={2} />
              <Brush dataKey="date" {...chartBrushStyle} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Resume Scrolls (Job Feed)" total={scrollsData?.total ?? 0} totalLabel="scrolls">
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={scrollsTrend}>
              <defs>
                <linearGradient id="scrollGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#14B8A6" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#14B8A6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={chartTick} axisLine={false} tickLine={false} />
              <YAxis tick={chartTick} axisLine={false} tickLine={false} width={30} />
              <Tooltip {...chartTooltipStyle} />
              <Area type="monotone" dataKey="scrolls" stroke="#14B8A6" fill="url(#scrollGrad)" strokeWidth={2} />
              <Brush dataKey="date" {...chartBrushStyle} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-5 rounded-xl border border-edge bg-surface-card/60">
          <h3 className="text-sm font-medium text-fg-secondary mb-3">Vacancies</h3>
          <p className="text-3xl font-bold text-fg">{kpi.total_vacancies.toLocaleString()}</p>
          <p className="text-xs text-fg-faint mt-1">Total indexed vacancies</p>
        </div>
        <div className="p-5 rounded-xl border border-edge bg-surface-card/60">
          <h3 className="text-sm font-medium text-fg-secondary mb-3">Resumes This Period</h3>
          <p className="text-3xl font-bold text-fg">{kpi.new_resumes_period}</p>
          <p className="text-xs text-fg-faint mt-1">Created in selected period</p>
        </div>
      </div>
    </div>
  );
}
