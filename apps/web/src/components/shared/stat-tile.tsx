import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatTileProps {
  label: string;
  value: string;
  icon?: LucideIcon;
  hint?: string;
  className?: string;
}

export function StatTile({ label, value, icon: Icon, hint, className }: StatTileProps) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-card p-4 sm:p-5 transition-colors",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm text-muted-foreground">{label}</span>
        {Icon ? <Icon className="size-4 text-muted-foreground/70" /> : null}
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-tight">{value}</div>
      {hint ? <div className="mt-1 text-xs text-muted-foreground">{hint}</div> : null}
    </div>
  );
}

export function StatTileSkeleton() {
  return (
    <div className="rounded-xl border bg-card p-4 sm:p-5">
      <div className="h-4 w-24 animate-pulse rounded bg-muted" />
      <div className="mt-3 h-7 w-16 animate-pulse rounded bg-muted" />
    </div>
  );
}
