import { cn } from "@/lib/utils";

interface MetricRowProps {
  label: string;
  value: React.ReactNode;
  className?: string;
}

/** A label/value line used inside metrics panels (training progress, eval detail, etc). */
export function MetricRow({ label, value, className }: MetricRowProps) {
  return (
    <div className={cn("flex items-center justify-between py-2 text-sm", className)}>
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: React.ReactNode;
  className?: string;
}

/** A compact metric tile used in grids (e.g. epoch, step, loss, GPU %). */
export function MetricCard({ label, value, className }: MetricCardProps) {
  return (
    <div className={cn("rounded-lg border bg-muted/30 px-3 py-2.5", className)}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-base font-semibold tabular-nums">{value}</div>
    </div>
  );
}
