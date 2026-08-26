"use client";

import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  cancelTrainingJob as apiCancelTrainingJob,
  createTrainingJob as apiCreateTrainingJob,
  getTrainingJob,
  getTrainingJobLogs,
  listTrainingJobs,
} from "@/lib/api";
import { useAsync } from "@/hooks/use-async";
import { isActiveTrainingStatus } from "@/lib/status";
import type { CreateTrainingJobInput, TrainingJobOut } from "@/lib/types";

const POLL_INTERVAL_MS = 4000;

export function useTrainingJobs() {
  return useAsync(() => listTrainingJobs(), []);
}

/**
 * Polls the job while it's in an active (queued/preparing/running/evaluating)
 * status, and stops automatically once it reaches a terminal status.
 */
export function useTrainingJob(id: string) {
  const [data, setData] = useState<TrainingJobOut | undefined>(undefined);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const dataRef = useRef<TrainingJobOut | undefined>(undefined);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    getTrainingJob(id)
      .then((job) => {
        if (cancelled) return;
        setData(job);
        dataRef.current = job;
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Failed to load this training job.",
        );
      })
      .finally(() => {
        if (!cancelled) setInitialLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, tick]);

  useEffect(() => {
    if (!id) return;
    const interval = setInterval(() => {
      const current = dataRef.current;
      if (current && !isActiveTrainingStatus(current.status)) return;
      setTick((t) => t + 1);
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [id]);

  const refetch = () => setTick((t) => t + 1);

  return { data, initialLoading: id ? initialLoading : false, error, refetch };
}

export function useTrainingJobLogs(id: string, status: string | undefined) {
  const isActive = status ? isActiveTrainingStatus(status) : true;
  return useAsync(() => getTrainingJobLogs(id), [id], {
    enabled: Boolean(id),
    pollIntervalMs: isActive ? POLL_INTERVAL_MS : undefined,
  });
}

export async function createTrainingJob(
  input: CreateTrainingJobInput,
): Promise<TrainingJobOut> {
  return apiCreateTrainingJob(input);
}

export async function cancelTrainingJob(id: string): Promise<TrainingJobOut> {
  return apiCancelTrainingJob(id);
}
