"use client";

import { Boxes } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RegisterModelDialog } from "@/components/models/register-model-dialog";
import { useBaseModels } from "@/hooks/use-models";
import { formatParamCount } from "@/lib/format";
import { getProviderLabel } from "@/lib/status";

export default function ModelsPage() {
  const { data, initialLoading, error, refetch } = useBaseModels();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Models"
        description="Base models registered for fine-tuning. Registered dynamically — none are hardcoded."
        actions={<RegisterModelDialog onRegistered={refetch} />}
      />

      {error ? (
        <InlineError message={error} onRetry={refetch} />
      ) : initialLoading ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={Boxes}
          title="No base models registered"
          description="Register a Hugging Face or local base model to start training against it."
          action={<RegisterModelDialog onRegistered={refetch} />}
        />
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((model) => (
            <Card key={model.id}>
              <CardContent className="flex flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">{model.name}</div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {getProviderLabel(model.provider)}
                      {model.architecture ? ` · ${model.architecture}` : ""}
                    </div>
                  </div>
                  <StatusBadge status={model.status} className="shrink-0" />
                </div>

                {model.huggingface_id ? (
                  <code className="truncate rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground">
                    {model.huggingface_id}
                  </code>
                ) : null}

                <div className="flex flex-wrap gap-1.5">
                  {model.parameter_count ? (
                    <Badge variant="secondary" className="font-normal">
                      {formatParamCount(model.parameter_count)} params
                    </Badge>
                  ) : null}
                  {model.context_length ? (
                    <Badge variant="secondary" className="font-normal">
                      {model.context_length.toLocaleString()} ctx
                    </Badge>
                  ) : null}
                  {model.quantization ? (
                    <Badge variant="secondary" className="font-normal">
                      {model.quantization}
                    </Badge>
                  ) : null}
                  {model.license ? (
                    <Badge variant="outline" className="font-normal">
                      {model.license}
                    </Badge>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
