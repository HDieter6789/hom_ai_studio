"use client";

import { useCallback, useEffect, useState } from "react";
import { clearToken, getCurrentUser, getToken } from "@/lib/api";
import type { User } from "@/lib/types";

export interface UseAuthResult {
  user: User | undefined;
  loading: boolean;
  error: string | null;
  hasToken: boolean;
  logout: () => void;
  refetch: () => void;
}

/**
 * Loads the current user from /api/auth/me using whatever token is in
 * localStorage. Pages/layouts use this both to render account info and to
 * gate access (redirecting to /login when there is no token at all).
 *
 * This hook is only ever rendered under `AuthGuard` (see
 * src/components/layout/auth-guard.tsx), which already prevents any of its
 * consumers from being part of the server-rendered / pre-hydration output.
 * That means reading localStorage synchronously here (for the initial
 * `loading` value) cannot cause a hydration mismatch.
 */
export function useAuth(): UseAuthResult {
  const [user, setUser] = useState<User | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(() => Boolean(getToken()));
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    let cancelled = false;
    // Standard "fetch in an effect" shape, see use-async.ts for details.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    getCurrentUser()
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load account.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tick]);

  const logout = useCallback(() => {
    clearToken();
    setUser(undefined);
    if (typeof window !== "undefined") {
      // Full reload (not a client-side route change) so any in-memory app
      // state tied to the previous session is discarded.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/login");
    }
  }, []);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  return { user, loading, error, hasToken: Boolean(getToken()), logout, refetch };
}
