import { MetricCard } from "@/components/shared/metric-row";
import { formatDecimal, formatNumber, formatPercent } from "@/lib/format";
import type { TrainingJobOut } from "@/lib/types";

interface MetricsPanelProps {
  job: TrainingJobOut;
}

export function MetricsPanel({ job }: MetricsPanelProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      <MetricCard
        label="Epoch"
        value={
          job.current_epoch !== null
            ? formatNumber(job.current_epoch)
            : "—"
        }
      />
      <MetricCard
        label="Step"
        value={
          job.current_step !== null
            ? `${formatNumber(job.current_step)}${job.total_steps ? ` / ${formatNumber(job.total_steps)}` : ""}`
            : "—"
        }
      />
      <MetricCard label="Loss" value={formatDecimal(job.loss, 4)} />
      <MetricCard label="Learning rate" value={job.learning_rate !== null ? job.learning_rate.toExponential(2) : "—"} />
      <MetricCard label="GPU memory" value={job.gpu_memory_used_gb !== null ? `${formatDecimal(job.gpu_memory_used_gb, 1)} GB` : "—"} />
      <MetricCard label="GPU utilization" value={formatPercent(job.gpu_utilization_pct)} />
      <MetricCard label="Samples / sec" value={formatDecimal(job.samples_per_sec, 2)} />
      <MetricCard label="Tokens / sec" value={formatNumber(job.tokens_per_sec)} />
    </div>
  );
}
