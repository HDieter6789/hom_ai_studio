import { AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrainingJobOut } from "@/lib/types";

interface TrainingErrorCardProps {
  job: TrainingJobOut;
}

/** Friendly rendering of a failed job's error_code/error_message/failed_step/suggested_actions — never a raw stack trace. */
export function TrainingErrorCard({ job }: TrainingErrorCardProps) {
  if (!job.error_message && !job.error_code) return null;

  return (
    <Card className="border-red-500/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertTriangle className="size-4" />
          Training failed
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          {job.error_code ? (
            <code className="w-fit rounded bg-red-500/10 px-1.5 py-0.5 font-mono text-xs text-red-600 dark:text-red-400">
              {job.error_code}
            </code>
          ) : null}
          <p className="text-sm">{job.error_message}</p>
          {job.failed_step ? (
            <p className="text-xs text-muted-foreground">Failed at step: {job.failed_step}</p>
          ) : null}
        </div>

        {job.suggested_actions.length > 0 ? (
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">
              Suggested actions
            </div>
            <ul className="flex flex-col gap-1.5 text-sm">
              {job.suggested_actions.map((action, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-muted-foreground">&bull;</span>
                  {action}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
