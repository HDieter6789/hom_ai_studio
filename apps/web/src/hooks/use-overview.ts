"use client";

import { getOverview } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";

export function useOverview() {
  return useAsync(() => getOverview(), []);
}
