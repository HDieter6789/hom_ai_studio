"use client";

import * as React from "react";
import { Loader2, MoreHorizontal } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StatusBadge } from "@/components/shared/status-badge";
import { ApiError, setModelVersionStatus } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { getStatusVisual } from "@/lib/status";
import type { ModelVersionOut, ModelVersionStatus } from "@/lib/types";

const ALL_STATUSES: ModelVersionStatus[] = [
  "experimental",
  "testing",
  "staging",
  "production",
  "archived",
];

interface VersionGroupProps {
  modelName: string;
  versions: ModelVersionOut[];
  onChanged?: () => void;
}

export function VersionGroup({ modelName, versions, onChanged }: VersionGroupProps) {
  const sorted = [...versions].sort((a, b) => b.version - a.version);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{modelName}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col divide-y">
        {sorted.map((version) => (
          <VersionRow key={version.id} version={version} onChanged={onChanged} />
        ))}
      </CardContent>
    </Card>
  );
}

function VersionRow({
  version,
  onChanged,
}: {
  version: ModelVersionOut;
  onChanged?: () => void;
}) {
  const [updating, setUpdating] = React.useState(false);

  async function handleStatusChange(status: ModelVersionStatus) {
    if (status === version.status) return;
    setUpdating(true);
    try {
      await setModelVersionStatus(version.id, status);
      toast.success(`${version.display_name} is now ${getStatusVisual(status).label}`);
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to update status.");
    } finally {
      setUpdating(false);
    }
  }

  return (
    <div className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{version.display_name}</span>
          <span className="text-xs text-muted-foreground">v{version.version}</span>
        </div>
        <div className="mt-0.5 text-xs text-muted-foreground">
          Created {formatDateTime(version.created_at)}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <StatusBadge status={version.status} />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="size-7" disabled={updating}>
              {updating ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <MoreHorizontal className="size-3.5" />
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {ALL_STATUSES.map((status) => (
              <DropdownMenuItem key={status} onClick={() => handleStatusChange(status)}>
                Mark as {getStatusVisual(status).label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
