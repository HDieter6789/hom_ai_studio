"use client";

import { getDataset, getDatasetPreview, listDatasets } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";

export function useDatasets() {
  return useAsync(() => listDatasets(), []);
}

export function useDataset(id: string) {
  return useAsync(() => getDataset(id), [id], { enabled: Boolean(id) });
}

export function useDatasetPreview(id: string, limit = 20) {
  return useAsync(() => getDatasetPreview(id, limit), [id, limit], {
    enabled: Boolean(id),
  });
}
