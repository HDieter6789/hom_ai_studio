"use client";

import Link from "next/link";
import { Plus, SlidersHorizontal } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TrainingJobRow } from "@/components/training/training-job-row";
import { useTrainingJobs } from "@/hooks/use-training";
import { useBaseModels } from "@/hooks/use-models";
import { useDatasets } from "@/hooks/use-datasets";

export default function TrainingJobsPage() {
  const { data, initialLoading, error, refetch } = useTrainingJobs();
  const { data: baseModels } = useBaseModels();
  const { data: datasets } = useDatasets();

  const modelNameById = new Map((baseModels ?? []).map((m) => [m.id, m.name]));
  const datasetNameById = new Map((datasets ?? []).map((d) => [d.id, d.name]));

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Training"
        description="Fine-tuning jobs for the HOM-CRM model family."
        actions={
          <Button size="sm" asChild>
            <Link href="/training/new">
              <Plus className="size-4" />
              New training run
            </Link>
          </Button>
        }
      />

      {error ? (
        <InlineError message={error} onRetry={refetch} />
      ) : initialLoading ? (
        <div className="flex flex-col gap-2.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={SlidersHorizontal}
          title="No training runs yet"
          description="Kick off a fine-tuning job against one of your registered base models and datasets."
          action={
            <Button size="sm" asChild>
              <Link href="/training/new">
                <Plus className="size-4" />
                New training run
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="flex flex-col gap-2.5">
          {data.map((job) => (
            <TrainingJobRow
              key={job.id}
              job={job}
              baseModelName={modelNameById.get(job.base_model_id)}
              datasetName={datasetNameById.get(job.dataset_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
