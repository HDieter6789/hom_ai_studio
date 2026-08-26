import Link from "next/link";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDecimal, formatPercent } from "@/lib/format";
import type { ModelVersionOut } from "@/lib/types";

interface ModelVersionSummaryCardProps {
  version: ModelVersionOut;
}

function metricValue(
  metrics: Record<string, unknown> | null | undefined,
  key: string,
): number | null {
  const raw = metrics?.[key];
  return typeof raw === "number" ? raw : null;
}

export function ModelVersionSummaryCard({ version }: ModelVersionSummaryCardProps) {
  const metrics = version.evaluation_metrics;
  const crmAccuracy = metricValue(metrics, "crm_accuracy");
  const toolAccuracy = metricValue(metrics, "tool_selection_accuracy");
  const latency = metricValue(metrics, "latency_ms");

  return (
    <Link
      href={`/registry?model_name=${encodeURIComponent(version.model_name)}`}
      className="flex flex-col gap-3 rounded-lg border p-3.5 transition-colors hover:bg-accent/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{version.display_name}</div>
          <div className="mt-0.5 text-xs text-muted-foreground">
            {version.model_name} &middot; v{version.version}
          </div>
        </div>
        <StatusBadge status={version.status} className="shrink-0" />
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded-md bg-muted/40 px-2 py-1.5">
          <div className="text-xs text-muted-foreground">CRM Acc.</div>
          <div className="text-sm font-semibold tabular-nums">
            {formatPercent(crmAccuracy, { alreadyRatio: crmAccuracy !== null && crmAccuracy <= 1 })}
          </div>
        </div>
        <div className="rounded-md bg-muted/40 px-2 py-1.5">
          <div className="text-xs text-muted-foreground">Tool Acc.</div>
          <div className="text-sm font-semibold tabular-nums">
            {formatPercent(toolAccuracy, { alreadyRatio: toolAccuracy !== null && toolAccuracy <= 1 })}
          </div>
        </div>
        <div className="rounded-md bg-muted/40 px-2 py-1.5">
          <div className="text-xs text-muted-foreground">Latency</div>
          <div className="text-sm font-semibold tabular-nums">
            {latency !== null ? `${formatDecimal(latency, 0)}ms` : "—"}
          </div>
        </div>
      </div>
    </Link>
  );
}

export function ModelVersionSummaryCardSkeleton() {
  return (
    <div className="flex flex-col gap-3 rounded-lg border p-3.5">
      <div className="flex items-center justify-between">
        <div className="h-4 w-32 animate-pulse rounded bg-muted" />
        <div className="h-5 w-20 animate-pulse rounded-full bg-muted" />
      </div>
      <div className="h-10 w-full animate-pulse rounded bg-muted" />
    </div>
  );
}
