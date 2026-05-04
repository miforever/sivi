"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";

export function useAnalytics<T = Record<string, unknown>>(
  endpoint: string,
  period: string = "30d",
  granularity?: string,
  extraParams?: Record<string, string>,
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const extraKey = extraParams ? JSON.stringify(extraParams) : "";

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ period });
      if (granularity) params.set("granularity", granularity);
      if (extraParams) {
        for (const [k, v] of Object.entries(extraParams)) {
          params.set(k, v);
        }
      }
      const result = await apiFetch<T>(`/analytics/${endpoint}/?${params.toString()}`);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, period, granularity, extraKey]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
