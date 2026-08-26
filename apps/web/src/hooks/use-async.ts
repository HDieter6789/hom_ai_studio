"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api";

export interface AsyncState<T> {
  data: T | undefined;
  loading: boolean;
  /** True only on the very first load (no data yet). Useful for skeletons vs. background refreshes. */
  initialLoading: boolean;
  error: string | null;
  refetch: () => void;
}

interface UseAsyncOptions {
  /** Poll interval in ms. When set (and >0), the fetcher re-runs on this cadence. */
  pollIntervalMs?: number;
  /** When false, skips fetching entirely (e.g. waiting on a required id). */
  enabled?: boolean;
}

/**
 * Generic data-fetching hook used by the domain-specific hooks in this
 * folder. Handles loading/error state and optional polling so individual
 * pages never talk to `src/lib/api.ts` directly.
 */
export function useAsync<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  options: UseAsyncOptions = {},
): AsyncState<T> {
  const { pollIntervalMs, enabled = true } = options;
  const [data, setData] = useState<T | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const fetcherRef = useRef(fetcher);

  // Keep the latest fetcher available to the effect below without making it
  // a reactive dependency (pages typically pass a fresh arrow function on
  // every render). Refs must be written outside of render, so this runs as
  // its own effect rather than inline in the component body.
  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    // This is the standard "fetch in an effect" shape from the React docs:
    // https://react.dev/reference/react/useEffect#fetching-data-with-effects
    // flip `loading` on right before kicking off the request, then resolve
    // it in the async callbacks below.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    fetcherRef
      .current()
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        const message =
          err instanceof ApiError
            ? err.message
            : "Something went wrong while loading this data.";
        setError(message);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
        setInitialLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, tick, ...deps]);

  useEffect(() => {
    if (!enabled || !pollIntervalMs || pollIntervalMs <= 0) return;
    const id = setInterval(() => {
      setTick((t) => t + 1);
    }, pollIntervalMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, pollIntervalMs, ...deps]);

  return { data, loading, initialLoading: enabled ? initialLoading : false, error, refetch };
}
