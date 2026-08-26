import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface InlineErrorProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

/** Friendly inline error used whenever an API call fails (e.g. backend unreachable). */
export function InlineError({
  title = "Couldn't load this data",
  message,
  onRetry,
  className,
}: InlineErrorProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed px-6 py-14 text-center",
        className,
      )}
    >
      <div className="mb-4 flex size-11 items-center justify-center rounded-full bg-red-500/10">
        <AlertTriangle className="size-5 text-red-600 dark:text-red-400" />
      </div>
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">{message}</p>
      {onRetry ? (
        <Button variant="outline" size="sm" className="mt-5" onClick={onRetry}>
          <RefreshCw className="size-3.5" />
          Try again
        </Button>
      ) : null}
    </div>
  );
}
