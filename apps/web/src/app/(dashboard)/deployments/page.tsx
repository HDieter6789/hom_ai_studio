"use client";

import { Rocket } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Skeleton } from "@/components/ui/skeleton";
import { DeployDialog } from "@/components/deployments/deploy-dialog";
import { DeploymentCard } from "@/components/deployments/deployment-card";
import { useDeployments } from "@/hooks/use-deployments";

export default function DeploymentsPage() {
  const { data, initialLoading, error, refetch } = useDeployments();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Deployments"
        description="Live model-serving endpoints."
        actions={<DeployDialog onDeployed={refetch} />}
      />

      {error ? (
        <InlineError message={error} onRetry={refetch} />
      ) : initialLoading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={Rocket}
          title="No deployments yet"
          description="Deploy a registered model version to serve an OpenAI-compatible endpoint."
          action={<DeployDialog onDeployed={refetch} />}
        />
      ) : (
        <div className="flex flex-col gap-3">
          {data.map((deployment) => (
            <DeploymentCard key={deployment.id} deployment={deployment} onChanged={refetch} />
          ))}
        </div>
      )}
    </div>
  );
}
