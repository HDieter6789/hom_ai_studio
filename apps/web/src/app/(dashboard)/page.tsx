"use client";

import Link from "next/link";
import {
  Boxes,
  Cpu,
  Database,
  FlaskConical,
  Gauge,
  Layers,
  Rocket,
  SlidersHorizontal,
  Trophy,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatTile, StatTileSkeleton } from "@/components/shared/stat-tile";
import { InlineError } from "@/components/shared/inline-error";
import { EmptyState } from "@/components/shared/empty-state";
import {
  TrainingJobRow,
  TrainingJobRowSkeleton,
} from "@/components/training/training-job-row";
import {
  ModelVersionSummaryCard,
  ModelVersionSummaryCardSkeleton,
} from "@/components/registry/model-version-summary-card";
import { useOverview } from "@/hooks/use-overview";
import { formatCompactNumber, formatNumber, formatPercent } from "@/lib/format";

export default function OverviewPage() {
  const { data, initialLoading, error, refetch } = useOverview();
  const stats = data?.stats;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Overview"
        description="A snapshot of your models, training activity, and infrastructure."
      />

      {error ? (
        <InlineError message={error} onRetry={refetch} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
            {initialLoading ? (
              Array.from({ length: 9 }).map((_, i) => <StatTileSkeleton key={i} />)
            ) : (
              <>
                <StatTile
                  label="Models"
                  value={formatNumber(stats?.models_total)}
                  icon={Boxes}
                />
                <StatTile
                  label="Production models"
                  value={formatNumber(stats?.production_models)}
                  icon={Trophy}
                />
                <StatTile
                  label="Active training jobs"
                  value={formatNumber(stats?.active_training_jobs)}
                  icon={SlidersHorizontal}
                />
                <StatTile
                  label="Training jobs (30d)"
                  value={formatNumber(stats?.training_jobs_last_30_days)}
                  icon={Layers}
                />
                <StatTile
                  label="Datasets stored"
                  value={formatNumber(stats?.datasets_total)}
                  icon={Database}
                />
                <StatTile
                  label="Training samples"
                  value={formatCompactNumber(stats?.training_samples_total)}
                  icon={FlaskConical}
                />
                <StatTile
                  label="GPU workers online"
                  value={`${formatNumber(stats?.gpu_workers_online)} / ${formatNumber(
                    stats?.gpu_workers_total,
                  )}`}
                  icon={Cpu}
                />
                <StatTile
                  label="Avg. GPU utilization"
                  value={
                    stats?.avg_gpu_utilization_pct != null
                      ? formatPercent(stats.avg_gpu_utilization_pct)
                      : "—"
                  }
                  icon={Gauge}
                />
                <StatTile
                  label="Active deployments"
                  value={formatNumber(stats?.active_deployments)}
                  icon={Rocket}
                />
              </>
            )}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">Recent training runs</h2>
                <Link href="/training" className="text-xs text-muted-foreground hover:text-foreground">
                  View all
                </Link>
              </div>
              <div className="flex flex-col gap-2.5">
                {initialLoading ? (
                  Array.from({ length: 3 }).map((_, i) => <TrainingJobRowSkeleton key={i} />)
                ) : data && data.recent_training_runs.length > 0 ? (
                  data.recent_training_runs.map((job) => (
                    <TrainingJobRow key={job.id} job={job} />
                  ))
                ) : (
                  <EmptyState
                    icon={SlidersHorizontal}
                    title="No training runs yet"
                    description="Start a new training job to see progress here."
                  />
                )}
              </div>
            </section>

            <section className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">Production models</h2>
                <Link href="/registry" className="text-xs text-muted-foreground hover:text-foreground">
                  View registry
                </Link>
              </div>
              <div className="flex flex-col gap-2.5">
                {initialLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <ModelVersionSummaryCardSkeleton key={i} />
                  ))
                ) : data && data.production_models.length > 0 ? (
                  data.production_models.map((version) => (
                    <ModelVersionSummaryCard key={version.id} version={version} />
                  ))
                ) : (
                  <EmptyState
                    icon={Trophy}
                    title="No production models yet"
                    description="Promote a model version to production from the Registry."
                  />
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
