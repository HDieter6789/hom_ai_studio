"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { EmptyState } from "@/components/shared/empty-state";
import { Terminal } from "lucide-react";
import type { TrainingLogEntry } from "@/lib/types";

interface LogViewerProps {
  logs: TrainingLogEntry[] | undefined;
  loading?: boolean;
}

const LEVEL_COLOR: Record<string, string> = {
  error: "text-red-400",
  warning: "text-amber-400",
  warn: "text-amber-400",
  info: "text-emerald-400",
  debug: "text-neutral-400",
};

export function LogViewer({ logs, loading }: LogViewerProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [logs?.length]);

  if (!loading && (!logs || logs.length === 0)) {
    return (
      <EmptyState
        icon={Terminal}
        title="No logs yet"
        description="Logs will appear here once the job starts producing output."
        className="rounded-lg"
      />
    );
  }

  return (
    <div
      ref={scrollRef}
      className="max-h-96 overflow-y-auto rounded-lg bg-neutral-950 p-4 font-mono text-xs leading-relaxed"
    >
      {(logs ?? []).map((entry, i) => (
        <div key={i} className="flex gap-3 whitespace-pre-wrap text-neutral-300">
          <span className="shrink-0 text-neutral-500">
            {new Date(entry.timestamp).toLocaleTimeString()}
          </span>
          <span
            className={cn(
              "shrink-0 uppercase",
              LEVEL_COLOR[entry.level?.toLowerCase()] ?? "text-neutral-400",
            )}
          >
            {entry.level}
          </span>
          <span className="min-w-0 break-words">{entry.message}</span>
        </div>
      ))}
    </div>
  );
}
