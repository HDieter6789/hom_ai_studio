"use client";

import * as React from "react";
import { Loader2, Square } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/status-badge";
import { CodeSnippet } from "@/components/shared/code-snippet";
import { ApiError, stopDeployment } from "@/lib/api";
import { formatDateTime, formatPercent } from "@/lib/format";
import type { DeploymentOut } from "@/lib/types";

interface DeploymentCardProps {
  deployment: DeploymentOut;
  onChanged?: () => void;
}

export function DeploymentCard({ deployment, onChanged }: DeploymentCardProps) {
  const [stopping, setStopping] = React.useState(false);
  const canStop = deployment.status !== "stopped" && deployment.status !== "failed";

  async function handleStop() {
    if (!window.confirm(`Stop deployment "${deployment.served_model_name}"?`)) return;
    setStopping(true);
    try {
      await stopDeployment(deployment.id);
      toast.success("Deployment stopped");
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to stop deployment.");
    } finally {
      setStopping(false);
    }
  }

  const snippet = deployment.endpoint_url
    ? `curl ${deployment.endpoint_url}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${deployment.served_model_name}",
    "messages": [{"role": "user", "content": "Hello"}]
  }'`
    : null;

  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium">{deployment.served_model_name}</div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              {deployment.worker_id ? `Worker ${deployment.worker_id}` : "Unassigned worker"}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <StatusBadge status={deployment.status} />
            {canStop ? (
              <Button variant="outline" size="sm" onClick={handleStop} disabled={stopping}>
                {stopping ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <Square className="size-3.5" />
                )}
                Stop
              </Button>
            ) : null}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
          <div>
            <div className="text-muted-foreground">GPU mem. util.</div>
            <div className="mt-0.5 font-medium tabular-nums">
              {deployment.gpu_memory_utilization !== null
                ? formatPercent(deployment.gpu_memory_utilization, { alreadyRatio: true })
                : "—"}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Max model len</div>
            <div className="mt-0.5 font-medium tabular-nums">
              {deployment.max_model_len ?? "—"}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Started</div>
            <div className="mt-0.5 font-medium">{formatDateTime(deployment.started_at)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Last health check</div>
            <div className="mt-0.5 font-medium">
              {formatDateTime(deployment.last_health_check_at)}
            </div>
          </div>
        </div>

        {deployment.last_health_detail ? (
          <p className="rounded-md bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
            {deployment.last_health_detail}
          </p>
        ) : null}

        {deployment.status === "healthy" && snippet ? (
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">
              POST /v1/chat/completions
            </div>
            <CodeSnippet code={snippet} />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
