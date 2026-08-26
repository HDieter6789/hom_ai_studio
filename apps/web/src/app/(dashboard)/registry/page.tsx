"use client";

import { Library } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Skeleton } from "@/components/ui/skeleton";
import { AliasPanel } from "@/components/registry/alias-panel";
import { VersionGroup } from "@/components/registry/version-group";
import { useModelAliases, useRegistryVersions } from "@/hooks/use-registry";
import type { ModelVersionOut } from "@/lib/types";

export default function RegistryPage() {
  const {
    data: versions,
    initialLoading: versionsLoading,
    error: versionsError,
    refetch: refetchVersions,
  } = useRegistryVersions();
  const {
    data: aliases,
    initialLoading: aliasesLoading,
    refetch: refetchAliases,
  } = useModelAliases();

  function refetchAll() {
    refetchVersions();
    refetchAliases();
  }

  const groups = new Map<string, ModelVersionOut[]>();
  for (const version of versions ?? []) {
    const list = groups.get(version.model_name) ?? [];
    list.push(version);
    groups.set(version.model_name, list);
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Registry"
        description="Model versions grouped by name, with status and alias management."
      />

      {!aliasesLoading && aliases ? (
        <AliasPanel aliases={aliases} versions={versions ?? []} onChanged={refetchAll} />
      ) : (
        <Skeleton className="h-32 rounded-xl" />
      )}

      {versionsError ? (
        <InlineError message={versionsError} onRetry={refetchVersions} />
      ) : versionsLoading ? (
        <div className="flex flex-col gap-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : groups.size === 0 ? (
        <EmptyState
          icon={Library}
          title="No model versions registered yet"
          description="Register a completed training run to create the first version."
        />
      ) : (
        <div className="flex flex-col gap-4">
          {Array.from(groups.entries()).map(([modelName, list]) => (
            <VersionGroup
              key={modelName}
              modelName={modelName}
              versions={list}
              onChanged={refetchAll}
            />
          ))}
        </div>
      )}
    </div>
  );
}
