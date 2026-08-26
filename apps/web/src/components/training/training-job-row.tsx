import Link from "next/link";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatRelativeTime } from "@/lib/format";
import { getTrainingPresetLabel } from "@/lib/status";
import { isActiveTrainingStatus } from "@/lib/status";
import type { TrainingJobOut } from "@/lib/types";

interface TrainingJobRowProps {
  job: TrainingJobOut;
  baseModelName?: string;
  datasetName?: string;
}

export function TrainingJobRow({ job, baseModelName, datasetName }: TrainingJobRowProps) {
  const showProgress = isActiveTrainingStatus(job.status);

  return (
    <Link
      href={`/training/${job.id}`}
      className="flex flex-col gap-2.5 rounded-lg border p-3.5 transition-colors hover:bg-accent/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{job.name}</div>
          <div className="mt-0.5 truncate text-xs text-muted-foreground">
            {baseModelName || "Base model"} &middot; {datasetName || "Dataset"} &middot;{" "}
            {getTrainingPresetLabel(job.preset)}
          </div>
        </div>
        <StatusBadge status={job.status} className="shrink-0" />
      </div>
      {showProgress ? (
        <div className="flex items-center gap-2.5">
          <Progress value={job.progress_pct ?? 0} className="h-1.5" />
          <span className="w-10 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
            {Math.round(job.progress_pct ?? 0)}%
          </span>
        </div>
      ) : (
        <div className="text-xs text-muted-foreground">
          {job.started_at
            ? `Started ${formatRelativeTime(job.started_at)}`
            : `Created ${formatRelativeTime(job.created_at)}`}
        </div>
      )}
    </Link>
  );
}

export function TrainingJobRowSkeleton() {
  return (
    <div className="flex flex-col gap-2.5 rounded-lg border p-3.5">
      <div className="flex items-center justify-between">
        <div className="h-4 w-40 animate-pulse rounded bg-muted" />
        <div className="h-5 w-16 animate-pulse rounded-full bg-muted" />
      </div>
      <div className="h-1.5 w-full animate-pulse rounded bg-muted" />
    </div>
  );
}
