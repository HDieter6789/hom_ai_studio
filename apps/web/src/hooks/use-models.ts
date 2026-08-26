"use client";

import { getBaseModel, listBaseModels } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";

export function useBaseModels() {
  return useAsync(() => listBaseModels(), []);
}

export function useBaseModel(id: string) {
  return useAsync(() => getBaseModel(id), [id], { enabled: Boolean(id) });
}
