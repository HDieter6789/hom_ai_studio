"use client";

import { listDeployments } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";

const POLL_INTERVAL_MS = 8000;

export function useDeployments() {
  return useAsync(() => listDeployments(), [], {
    pollIntervalMs: POLL_INTERVAL_MS,
  });
}
