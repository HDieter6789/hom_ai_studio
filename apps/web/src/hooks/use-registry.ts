"use client";

import { listModelAliases, listRegistryVersions } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";

export function useRegistryVersions(modelName?: string) {
  return useAsync(() => listRegistryVersions(modelName), [modelName]);
}

export function useModelAliases() {
  return useAsync(() => listModelAliases(), []);
}
