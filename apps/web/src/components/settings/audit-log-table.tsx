import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollText } from "lucide-react";
import { formatDateTime } from "@/lib/format";
import type { AuditLogEntry } from "@/lib/types";

interface AuditLogTableProps {
  entries: AuditLogEntry[] | undefined;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export function AuditLogTable({ entries, loading, error, onRetry }: AuditLogTableProps) {
  if (error) return <InlineError message={error} onRetry={onRetry} />;

  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!entries || entries.length === 0) {
    return (
      <EmptyState
        icon={ScrollText}
        title="No audit events yet"
        description="Actions taken across the platform will be recorded here."
      />
    );
  }

  return (
    <div className="rounded-xl border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Action</TableHead>
            <TableHead>Actor</TableHead>
            <TableHead>Target</TableHead>
            <TableHead className="text-right">Timestamp</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entries.map((entry) => (
            <TableRow key={entry.id}>
              <TableCell className="font-medium">{entry.action}</TableCell>
              <TableCell className="text-muted-foreground">{entry.actor ?? "—"}</TableCell>
              <TableCell className="text-muted-foreground">
                {entry.target_type ? `${entry.target_type}${entry.target_id ? ` · ${entry.target_id}` : ""}` : "—"}
              </TableCell>
              <TableCell className="text-right text-muted-foreground">
                {formatDateTime(entry.timestamp)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
