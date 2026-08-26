"use client";

import * as React from "react";
import { Loader2, Rocket } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
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
import { ApiError, createDeployment } from "@/lib/api";
import { useRegistryVersions } from "@/hooks/use-registry";
import type { DeploymentOut } from "@/lib/types";

interface DeployDialogProps {
  onDeployed?: (deployment: DeploymentOut) => void;
}

export function DeployDialog({ onDeployed }: DeployDialogProps) {
  const { data: versions } = useRegistryVersions();
  const [open, setOpen] = React.useState(false);
  const [versionId, setVersionId] = React.useState("");
  const [servedName, setServedName] = React.useState("");
  const [gpuMemUtil, setGpuMemUtil] = React.useState("0.85");
  const [maxModelLen, setMaxModelLen] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  function reset() {
    setVersionId("");
    setServedName("");
    setGpuMemUtil("0.85");
    setMaxModelLen("");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const deployment = await createDeployment({
        model_version_id: versionId,
        served_model_name: servedName,
        gpu_memory_utilization: Number(gpuMemUtil),
        max_model_len: maxModelLen ? Number(maxModelLen) : undefined,
      });
      toast.success(`Deployment "${deployment.served_model_name}" started`);
      onDeployed?.(deployment);
      setOpen(false);
      reset();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start deployment.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm">
          <Rocket className="size-4" />
          Deploy model
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Deploy model</DialogTitle>
            <DialogDescription>
              Serves an OpenAI-compatible endpoint for the selected model version.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="deploy-version">Model version</Label>
              <Select value={versionId} onValueChange={setVersionId}>
                <SelectTrigger id="deploy-version" className="w-full">
                  <SelectValue placeholder="Select a version" />
                </SelectTrigger>
                <SelectContent>
                  {(versions ?? []).map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="deploy-served-name">Served model name</Label>
              <Input
                id="deploy-served-name"
                value={servedName}
                onChange={(e) => setServedName(e.target.value)}
                placeholder="hom-crm-v3"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="deploy-gpu-mem">GPU memory utilization</Label>
                <Input
                  id="deploy-gpu-mem"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={gpuMemUtil}
                  onChange={(e) => setGpuMemUtil(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="deploy-max-len">Max model length</Label>
                <Input
                  id="deploy-max-len"
                  type="number"
                  value={maxModelLen}
                  onChange={(e) => setMaxModelLen(e.target.value)}
                  placeholder="Optional"
                />
              </div>
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
              Deploy
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
