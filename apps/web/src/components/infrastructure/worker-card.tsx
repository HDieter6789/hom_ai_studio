import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDecimal, formatRelativeTime } from "@/lib/format";
import { getProviderLabel } from "@/lib/status";
import type { WorkerOut } from "@/lib/types";

interface WorkerCardProps {
  worker: WorkerOut;
}

export function WorkerCard({ worker }: WorkerCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium">{worker.hostname || worker.worker_key}</div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              {worker.worker_key} &middot; {getProviderLabel(worker.compute_provider)}
            </div>
          </div>
          <StatusBadge status={worker.status} className="shrink-0" />
        </div>

        {worker.gpus.length === 0 ? (
          <p className="text-xs text-muted-foreground">No GPU telemetry reported.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {worker.gpus.map((gpu) => {
              const usedPct =
                gpu.vram_total_gb > 0 ? (gpu.vram_used_gb / gpu.vram_total_gb) * 100 : 0;
              return (
                <div key={gpu.index} className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium">
                      GPU {gpu.index} &middot; {gpu.name}
                    </span>
                    <span className="text-muted-foreground">
                      {formatDecimal(gpu.vram_used_gb, 1)} / {formatDecimal(gpu.vram_total_gb, 1)} GB
                    </span>
                  </div>
                  <Progress value={usedPct} className="h-1.5" />
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{Math.round(gpu.utilization_pct)}% utilization</span>
                    {gpu.temperature_c !== null ? <span>{Math.round(gpu.temperature_c)}&deg;C</span> : null}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
          <span>
            {worker.running_job_id ? `Running job ${worker.running_job_id}` : "Idle"}
          </span>
          <span>
            {worker.last_heartbeat_at
              ? `Heartbeat ${formatRelativeTime(worker.last_heartbeat_at)}`
              : "No heartbeat"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
