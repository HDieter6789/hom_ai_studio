"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { AlertTriangle, ArrowLeft, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { InlineError } from "@/components/shared/inline-error";
import { EmptyState } from "@/components/shared/empty-state";
import { MetricCard } from "@/components/shared/metric-row";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDataset, useDatasetPreview } from "@/hooks/use-datasets";
import { deleteDataset, ApiError } from "@/lib/api";
import { formatBytes, formatDateTime, formatNumber } from "@/lib/format";
import { getDatasetTypeLabel } from "@/lib/status";

export default function DatasetDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const { data: dataset, initialLoading, error, refetch } = useDataset(id);
  const { data: preview, initialLoading: previewLoading } = useDatasetPreview(id, 20);
  const [deleting, setDeleting] = React.useState(false);

  async function handleDelete() {
    if (!dataset) return;
    if (!window.confirm(`Delete dataset "${dataset.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await deleteDataset(dataset.id);
      toast.success("Dataset deleted");
      router.push("/datasets");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to delete dataset.");
    } finally {
      setDeleting(false);
    }
  }

  if (error) {
    return (
      <div className="flex flex-col gap-6">
        <Button variant="ghost" size="sm" className="w-fit" onClick={() => router.push("/datasets")}>
          <ArrowLeft className="size-4" />
          Back to datasets
        </Button>
        <InlineError message={error} onRetry={refetch} />
      </div>
    );
  }

  if (initialLoading || !dataset) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  const stats = dataset.stats;
  const schema = dataset.schema_info;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Button
          variant="ghost"
          size="sm"
          className="mb-3 -ml-2"
          onClick={() => router.push("/datasets")}
        >
          <ArrowLeft className="size-4" />
          Back to datasets
        </Button>
        <PageHeader
          title={dataset.name}
          description={dataset.description || undefined}
          actions={
            <>
              <StatusBadge status={dataset.status} />
              <Button
                variant="outline"
                size="sm"
                onClick={handleDelete}
                disabled={deleting}
                className="text-red-600 hover:text-red-600 dark:text-red-400"
              >
                {deleting ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
                Delete
              </Button>
            </>
          }
        />
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Badge variant="secondary" className="font-normal">
            {getDatasetTypeLabel(dataset.type)}
          </Badge>
          <Badge variant="outline" className="font-normal uppercase">
            {dataset.format}
          </Badge>
          <span className="text-xs text-muted-foreground">v{dataset.version}</span>
          <span className="text-xs text-muted-foreground">&middot;</span>
          <span className="text-xs text-muted-foreground">
            Updated {formatDateTime(dataset.updated_at)}
          </span>
        </div>
      </div>

      {dataset.validation_errors.length > 0 ? (
        <Card className="border-red-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertTriangle className="size-4" />
              Validation errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-1.5 text-sm text-muted-foreground">
              {dataset.validation_errors.map((err, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-red-500">&bull;</span>
                  {err}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <section>
        <h2 className="mb-3 text-sm font-semibold">Statistics</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <MetricCard label="Sample count" value={formatNumber(stats?.sample_count ?? dataset.sample_count)} />
          <MetricCard label="Valid" value={formatNumber(stats?.valid_count)} />
          <MetricCard label="Invalid" value={formatNumber(stats?.invalid_count)} />
          <MetricCard label="Possible duplicates" value={formatNumber(stats?.possible_duplicates)} />
          <MetricCard label="Avg tokens" value={formatNumber(stats?.avg_tokens)} />
          <MetricCard label="Min tokens" value={formatNumber(stats?.min_tokens)} />
          <MetricCard label="Max tokens" value={formatNumber(stats?.max_tokens)} />
          <MetricCard label="File size" value={formatBytes(dataset.file_size_bytes)} />
        </div>
      </section>

      {schema ? (
        <section>
          <h2 className="mb-3 text-sm font-semibold">Schema</h2>
          <Card>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-wrap gap-2">
                {schema.detected_format ? (
                  <Badge variant="secondary" className="font-normal">
                    Format: {schema.detected_format}
                  </Badge>
                ) : null}
                {schema.has_messages ? <Badge variant="outline">has_messages</Badge> : null}
                {schema.has_tool_calls ? <Badge variant="outline">has_tool_calls</Badge> : null}
                {schema.has_trajectory_fields ? (
                  <Badge variant="outline">has_trajectory_fields</Badge>
                ) : null}
              </div>
              {schema.fields.length > 0 ? (
                <div>
                  <div className="mb-1.5 text-xs text-muted-foreground">Detected fields</div>
                  <div className="flex flex-wrap gap-1.5">
                    {schema.fields.map((f) => (
                      <code
                        key={f}
                        className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs"
                      >
                        {f}
                      </code>
                    ))}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </section>
      ) : null}

      <section>
        <h2 className="mb-3 text-sm font-semibold">Sample preview</h2>
        {previewLoading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
        ) : !preview || preview.samples.length === 0 ? (
          <EmptyState title="No preview available" description="This dataset has no sample preview yet." />
        ) : (
          <div className="flex flex-col gap-3">
            {preview.samples.map((sample, i) => (
              <pre
                key={i}
                className="max-h-72 overflow-auto rounded-lg border bg-muted/30 p-3.5 font-mono text-xs leading-relaxed"
              >
                {JSON.stringify(sample, null, 2)}
              </pre>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
