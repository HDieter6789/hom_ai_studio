"use client";

import * as React from "react";
import { ArrowRight, Minus, TrendingDown, TrendingUp } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Skeleton } from "@/components/ui/skeleton";
import { useEvaluationCompare } from "@/hooks/use-evaluations";
import { formatDecimal } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ModelVersionOut } from "@/lib/types";

// Metrics where a lower value is better (e.g. hallucination rate, latency).
const LOWER_IS_BETTER = new Set(["hallucination_rate", "latency_ms"]);

function metricLabel(key: string): string {
  return key
    .split("_")
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(" ");
}

interface CompareViewProps {
  versions: ModelVersionOut[];
}

export function CompareView({ versions }: CompareViewProps) {
  const [versionA, setVersionA] = React.useState("");
  const [versionB, setVersionB] = React.useState("");
  const { data, loading, error, compare } = useEvaluationCompare();

  React.useEffect(() => {
    if (versionA && versionB && versionA !== versionB) {
      compare(versionA, versionB);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versionA, versionB]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-3 sm:flex-row">
        <div className="flex w-full flex-col gap-1.5 sm:w-64">
          <Label>Version A</Label>
          <Select value={versionA} onValueChange={setVersionA}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a version" />
            </SelectTrigger>
            <SelectContent>
              {versions.map((v) => (
                <SelectItem key={v.id} value={v.id}>
                  {v.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <ArrowRight className="mt-5 hidden size-4 shrink-0 text-muted-foreground sm:block" />
        <div className="flex w-full flex-col gap-1.5 sm:w-64">
          <Label>Version B</Label>
          <Select value={versionB} onValueChange={setVersionB}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a version" />
            </SelectTrigger>
            <SelectContent>
              {versions.map((v) => (
                <SelectItem key={v.id} value={v.id}>
                  {v.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {!versionA || !versionB ? (
        <EmptyState title="Pick two versions to compare" description="Select a version on each side to see a metrics diff." />
      ) : versionA === versionB ? (
        <EmptyState title="Pick two different versions" description="Version A and B must be different." />
      ) : error ? (
        <InlineError message={error} onRetry={() => compare(versionA, versionB)} />
      ) : loading || !data ? (
        <Skeleton className="h-64 rounded-xl" />
      ) : (
        <div className="overflow-hidden rounded-xl border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-left">
                <th className="px-4 py-2.5 font-medium">Metric</th>
                <th className="px-4 py-2.5 font-medium">{data.a.display_name}</th>
                <th className="px-4 py-2.5 font-medium">{data.b.display_name}</th>
                <th className="px-4 py-2.5 font-medium">Delta</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.metrics).map(([key, val]) => {
                const lowerIsBetter = LOWER_IS_BETTER.has(key);
                const delta = val.delta;
                const improved = delta !== null && (lowerIsBetter ? delta < 0 : delta > 0);
                const regressed = delta !== null && (lowerIsBetter ? delta > 0 : delta < 0);
                return (
                  <tr key={key} className="border-b last:border-0">
                    <td className="px-4 py-2.5 text-muted-foreground">{metricLabel(key)}</td>
                    <td className="px-4 py-2.5 tabular-nums">{formatDecimal(val.a, 3)}</td>
                    <td className="px-4 py-2.5 tabular-nums">{formatDecimal(val.b, 3)}</td>
                    <td
                      className={cn(
                        "px-4 py-2.5 tabular-nums font-medium",
                        improved && "text-emerald-600 dark:text-emerald-400",
                        regressed && "text-red-600 dark:text-red-400",
                      )}
                    >
                      <span className="inline-flex items-center gap-1">
                        {delta === null ? (
                          <Minus className="size-3" />
                        ) : improved ? (
                          <TrendingUp className="size-3" />
                        ) : regressed ? (
                          <TrendingDown className="size-3" />
                        ) : (
                          <Minus className="size-3" />
                        )}
                        {delta !== null ? `${delta > 0 ? "+" : ""}${formatDecimal(delta, 3)}` : "—"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
