"use client";

import { listWorkers } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";

const POLL_INTERVAL_MS = 8000;

export function useWorkers() {
  return useAsync(() => listWorkers(), [], { pollIntervalMs: POLL_INTERVAL_MS });
}
