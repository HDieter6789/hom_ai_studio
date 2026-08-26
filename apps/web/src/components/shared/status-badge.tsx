import { cn } from "@/lib/utils";
import { getStatusVisual, toneClassNames, toneDotClassNames } from "@/lib/status";

interface StatusBadgeProps {
  status: string | null | undefined;
  className?: string;
  /** Show a small colored dot instead of a filled pill. */
  variant?: "pill" | "dot";
}

export function StatusBadge({ status, className, variant = "pill" }: StatusBadgeProps) {
  const { label, tone } = getStatusVisual(status);

  if (variant === "dot") {
    return (
      <span className={cn("inline-flex items-center gap-1.5 text-sm", className)}>
        <span className={cn("size-1.5 rounded-full", toneDotClassNames[tone])} />
        {label}
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        toneClassNames[tone],
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", toneDotClassNames[tone])} />
      {label}
    </span>
  );
}
