"use client";

import { Cpu } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Skeleton } from "@/components/ui/skeleton";
import { WorkerCard } from "@/components/infrastructure/worker-card";
import { useWorkers } from "@/hooks/use-workers";

export default function InfrastructurePage() {
  const { data, initialLoading, error, refetch } = useWorkers();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Infrastructure"
        description="GPU workers available for training and inference."
      />

      {error ? (
        <InlineError message={error} onRetry={refetch} />
      ) : initialLoading ? (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={Cpu}
          title="No GPU workers registered"
          description="Workers will appear here once they connect and start sending heartbeats."
        />
      ) : (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {data.map((worker) => (
            <WorkerCard key={worker.id} worker={worker} />
          ))}
        </div>
      )}
    </div>
  );
}
