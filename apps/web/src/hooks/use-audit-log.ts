"use client";

import { listAuditLog } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";

export function useAuditLog(limit = 100, enabled = true) {
  return useAsync(() => listAuditLog(limit), [limit], { enabled });
}
