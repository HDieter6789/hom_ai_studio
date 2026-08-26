"use client";

import { useCallback, useState } from "react";
import { compareEvaluations, listEvaluations } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";
import type { EvaluationCompareOut } from "@/lib/types";
import { ApiError } from "@/lib/api";

export function useEvaluations(modelVersionId?: string) {
  return useAsync(() => listEvaluations(modelVersionId), [modelVersionId]);
}

export function useEvaluationCompare() {
  const [data, setData] = useState<EvaluationCompareOut | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const compare = useCallback(async (versionIdA: string, versionIdB: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await compareEvaluations(versionIdA, versionIdB);
      setData(result);
      return result;
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to compare versions.",
      );
      setData(undefined);
      return undefined;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, compare };
}
