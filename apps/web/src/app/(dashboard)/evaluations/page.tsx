"use client";

import { FlaskConical } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/inline-error";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CompareView } from "@/components/evaluations/compare-view";
import { useEvaluations } from "@/hooks/use-evaluations";
import { useRegistryVersions } from "@/hooks/use-registry";
import { formatDateTime, formatDecimal, formatNumber } from "@/lib/format";

export default function EvaluationsPage() {
  const { data: evaluations, initialLoading, error, refetch } = useEvaluations();
  const { data: versions } = useRegistryVersions();

  const versionById = new Map((versions ?? []).map((v) => [v.id, v]));

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Evaluations"
        description="Benchmark results for registered model versions."
      />

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All evaluations</TabsTrigger>
          <TabsTrigger value="compare">Compare versions</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          {error ? (
            <InlineError message={error} onRetry={refetch} />
          ) : initialLoading ? (
            <div className="flex flex-col gap-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          ) : !evaluations || evaluations.length === 0 ? (
            <EmptyState
              icon={FlaskConical}
              title="No evaluations yet"
              description="Evaluations recorded against a model version will show up here."
            />
          ) : (
            <div className="rounded-xl border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Version</TableHead>
                    <TableHead className="text-right">CRM Acc.</TableHead>
                    <TableHead className="text-right">Tool Acc.</TableHead>
                    <TableHead className="text-right">Hallucination</TableHead>
                    <TableHead className="text-right">Latency (ms)</TableHead>
                    <TableHead className="text-right">Samples</TableHead>
                    <TableHead className="text-right">Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {evaluations.map((evaluation) => (
                    <TableRow key={evaluation.id}>
                      <TableCell className="font-medium">
                        {versionById.get(evaluation.model_version_id)?.display_name ||
                          evaluation.model_version_id}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatDecimal(evaluation.metrics.crm_accuracy, 3)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatDecimal(evaluation.metrics.tool_selection_accuracy, 3)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatDecimal(evaluation.metrics.hallucination_rate, 3)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatDecimal(evaluation.metrics.latency_ms, 0)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {formatNumber(evaluation.sample_count)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatDateTime(evaluation.created_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        <TabsContent value="compare" className="mt-4">
          {!versions || versions.length < 2 ? (
            <EmptyState
              title="Need at least two versions"
              description="Register more model versions to compare their evaluation metrics."
            />
          ) : (
            <CompareView versions={versions} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
