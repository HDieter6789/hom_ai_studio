"use client";

import * as React from "react";
import { Loader2, Tag } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/shared/empty-state";
import { ApiError, setModelAlias } from "@/lib/api";
import type { ModelAliasOut, ModelVersionOut } from "@/lib/types";

interface AliasPanelProps {
  aliases: ModelAliasOut[];
  versions: ModelVersionOut[];
  onChanged?: () => void;
}

export function AliasPanel({ aliases, versions, onChanged }: AliasPanelProps) {
  const versionById = new Map(versions.map((v) => [v.id, v]));

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm">Aliases</CardTitle>
        <SetAliasDialog versions={versions} onChanged={onChanged} />
      </CardHeader>
      <CardContent>
        {aliases.length === 0 ? (
          <EmptyState
            icon={Tag}
            title="No aliases set"
            description="Point a friendly name like hom-crm-production at a specific version."
            className="py-8"
          />
        ) : (
          <div className="flex flex-wrap gap-2">
            {aliases.map((alias) => {
              const version = versionById.get(alias.model_version_id);
              return (
                <Badge key={alias.alias} variant="secondary" className="gap-1.5 py-1.5 font-normal">
                  <span className="font-medium">{alias.alias}</span>
                  <span className="text-muted-foreground">&rarr;</span>
                  <span>{version?.display_name || alias.model_version_id}</span>
                </Badge>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SetAliasDialog({
  versions,
  onChanged,
}: {
  versions: ModelVersionOut[];
  onChanged?: () => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [alias, setAlias] = React.useState("hom-crm-latest");
  const [versionId, setVersionId] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await setModelAlias({ alias, model_version_id: versionId });
      toast.success(`Alias "${alias}" updated`);
      onChanged?.();
      setOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to set alias.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Tag className="size-4" />
          Set alias
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-sm">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Set alias</DialogTitle>
            <DialogDescription>
              e.g. hom-crm-latest, hom-crm-production, hom-crm-staging
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="alias-name">Alias</Label>
              <Input
                id="alias-name"
                value={alias}
                onChange={(e) => setAlias(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="alias-version">Model version</Label>
              <Select value={versionId} onValueChange={setVersionId}>
                <SelectTrigger id="alias-version" className="w-full">
                  <SelectValue placeholder="Select a version" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {error ? (
              <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || !versionId}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
