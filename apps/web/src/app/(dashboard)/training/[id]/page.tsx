"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, Loader2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { InlineError } from "@/components/shared/inline-error";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricsPanel } from "@/components/training/metrics-panel";
import { LogViewer } from "@/components/training/log-viewer";
import { TrainingErrorCard } from "@/components/training/training-error-card";
import { RegisterVersionDialog } from "@/components/training/register-version-dialog";
import { useTrainingJob, useTrainingJobLogs, cancelTrainingJob } from "@/hooks/use-training";
import { useBaseModel } from "@/hooks/use-models";
import { useDataset } from "@/hooks/use-datasets";
import { formatDateTime } from "@/lib/format";
import { getTrainingPresetLabel, getTrainingTypeLabel, isActiveTrainingStatus } from "@/lib/status";
import { ApiError } from "@/lib/api";

export default function TrainingJobDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();

  const { data: job, initialLoading, error, refetch } = useTrainingJob(id);
  const { data: logs, initialLoading: logsLoading } = useTrainingJobLogs(id, job?.status);
  const { data: baseModel } = useBaseModel(job?.base_model_id ?? "");
  const { data: dataset } = useDataset(job?.dataset_id ?? "");
  const [cancelling, setCancelling] = React.useState(false);

  async function handleCancel() {
    if (!job) return;
    setCancelling(true);
    try {
      await cancelTrainingJob(job.id);
      toast.success("Training job cancelled");
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to cancel job.");
    } finally {
      setCancelling(false);
    }
  }

  if (error) {
    return (
      <div className="flex flex-col gap-6">
        <Button variant="ghost" size="sm" className="w-fit" onClick={() => router.push("/training")}>
          <ArrowLeft className="size-4" />
          Back to training
        </Button>
        <InlineError message={error} onRetry={refetch} />
      </div>
    );
  }

  if (initialLoading || !job) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-24 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  const active = isActiveTrainingStatus(job.status);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Button variant="ghost" size="sm" className="mb-3 -ml-2" onClick={() => router.push("/training")}>
          <ArrowLeft className="size-4" />
          Back to training
        </Button>
        <PageHeader
          title={job.name}
          description={`${baseModel?.name || "Base model"} · ${dataset?.name || "Dataset"} · ${getTrainingPresetLabel(job.preset)} · ${getTrainingTypeLabel(job.training_type)}`}
          actions={
            <>
              <StatusBadge status={job.status} />
              {active ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancel}
                  disabled={cancelling}
                  className="text-red-600 hover:text-red-600 dark:text-red-400"
                >
                  {cancelling ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <XCircle className="size-4" />
                  )}
                  Cancel
                </Button>
              ) : null}
              {job.status === "completed" ? <RegisterVersionDialog trainingJobId={job.id} /> : null}
            </>
          }
        />
      </div>

      {active ? (
        <Card>
          <CardContent className="flex flex-col gap-2.5">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Progress</span>
              <span className="tabular-nums text-muted-foreground">
                {Math.round(job.progress_pct ?? 0)}%
              </span>
            </div>
            <Progress value={job.progress_pct ?? 0} />
          </CardContent>
        </Card>
      ) : null}

      <TrainingErrorCard job={job} />

      <section>
        <h2 className="mb-3 text-sm font-semibold">Metrics</h2>
        <MetricsPanel job={job} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold">Logs</h2>
        <LogViewer logs={logs} loading={logsLoading} />
      </section>

      <section>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Run details</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            <DetailField label="Provider" value={job.provider ?? "—"} />
            <DetailField label="Worker" value={job.worker_id ?? "—"} />
            <DetailField label="Created" value={formatDateTime(job.created_at)} />
            <DetailField label="Started" value={formatDateTime(job.started_at)} />
            <DetailField label="Completed" value={formatDateTime(job.completed_at)} />
            <DetailField label="Output dir" value={job.output_dir ?? "—"} />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-0.5 truncate font-medium">{value}</div>
    </div>
  );
}
