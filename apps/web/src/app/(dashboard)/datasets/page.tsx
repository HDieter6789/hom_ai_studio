"use client";

import Link from "next/link";
import { Database } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
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
import { Badge } from "@/components/ui/badge";
import { UploadDatasetDialog } from "@/components/datasets/upload-dataset-dialog";
import { useDatasets } from "@/hooks/use-datasets";
import { formatBytes, formatNumber, formatRelativeTime } from "@/lib/format";
import { getDatasetTypeLabel } from "@/lib/status";

export default function DatasetsPage() {
  const { data, initialLoading, error, refetch } = useDatasets();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Datasets"
        description="Training and evaluation data registered with H.O.M AI Studio."
        actions={<UploadDatasetDialog onUploaded={refetch} />}
      />

      {error ? (
        <InlineError message={error} onRetry={refetch} />
      ) : initialLoading ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No datasets yet"
          description="Upload a .json, .jsonl or .csv file to get started."
          action={<UploadDatasetDialog onUploaded={refetch} />}
        />
      ) : (
        <div className="rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Samples</TableHead>
                <TableHead className="text-right">Size</TableHead>
                <TableHead className="text-right">Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((dataset) => (
                <TableRow key={dataset.id} className="cursor-pointer">
                  <TableCell className="whitespace-normal">
                    <Link href={`/datasets/${dataset.id}`} className="block">
                      <div className="font-medium text-foreground">{dataset.name}</div>
                      {dataset.description ? (
                        <div className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
                          {dataset.description}
                        </div>
                      ) : null}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="font-normal">
                      {getDatasetTypeLabel(dataset.type)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={dataset.status} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(dataset.sample_count)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-muted-foreground">
                    {formatBytes(dataset.file_size_bytes)}
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {formatRelativeTime(dataset.updated_at)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
