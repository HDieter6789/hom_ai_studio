"use client";

import * as React from "react";
import { Loader2, Plus } from "lucide-react";
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
import { ApiError, createBaseModel } from "@/lib/api";
import { PROVIDER_LABELS } from "@/lib/status";
import type { BaseModelOut, ModelProvider } from "@/lib/types";

interface RegisterModelDialogProps {
  onRegistered?: (model: BaseModelOut) => void;
}

const PROVIDERS: ModelProvider[] = ["qwen", "mistral", "llama", "gemma", "other"];

export function RegisterModelDialog({ onRegistered }: RegisterModelDialogProps) {
  const [open, setOpen] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [name, setName] = React.useState("");
  const [provider, setProvider] = React.useState<ModelProvider>("qwen");
  const [huggingfaceId, setHuggingfaceId] = React.useState("");
  const [architecture, setArchitecture] = React.useState("");
  const [parameterCount, setParameterCount] = React.useState("");
  const [contextLength, setContextLength] = React.useState("");
  const [license, setLicense] = React.useState("");
  const [quantization, setQuantization] = React.useState("");
  const [localPath, setLocalPath] = React.useState("");

  function reset() {
    setName("");
    setProvider("qwen");
    setHuggingfaceId("");
    setArchitecture("");
    setParameterCount("");
    setContextLength("");
    setLicense("");
    setQuantization("");
    setLocalPath("");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const model = await createBaseModel({
        name,
        provider,
        huggingface_id: huggingfaceId || undefined,
        architecture: architecture || undefined,
        parameter_count: parameterCount ? Number(parameterCount) : undefined,
        context_length: contextLength ? Number(contextLength) : undefined,
        license: license || undefined,
        quantization: quantization || undefined,
        local_path: localPath || undefined,
      });
      toast.success(`Model "${model.name}" registered`);
      onRegistered?.(model);
      setOpen(false);
      reset();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to register model.");
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
          <Plus className="size-4" />
          Register model
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Register base model</DialogTitle>
            <DialogDescription>
              Base models are registered dynamically — nothing is hardcoded.
              Point to a Hugging Face repo or a local path.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="col-span-2 flex flex-col gap-1.5">
              <Label htmlFor="model-name">Name</Label>
              <Input
                id="model-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Qwen2.5-7B-Instruct"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="model-provider">Provider</Label>
              <Select value={provider} onValueChange={(v) => setProvider(v as ModelProvider)}>
                <SelectTrigger id="model-provider" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PROVIDERS.map((p) => (
                    <SelectItem key={p} value={p}>
                      {PROVIDER_LABELS[p]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="model-hf-id">Hugging Face ID</Label>
              <Input
                id="model-hf-id"
                value={huggingfaceId}
                onChange={(e) => setHuggingfaceId(e.target.value)}
                placeholder="Qwen/Qwen2.5-7B-Instruct"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="model-architecture">Architecture</Label>
              <Input
                id="model-architecture"
                value={architecture}
                onChange={(e) => setArchitecture(e.target.value)}
                placeholder="qwen2"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="model-params">Parameter count</Label>
              <Input
                id="model-params"
                type="number"
                value={parameterCount}
                onChange={(e) => setParameterCount(e.target.value)}
                placeholder="7000000000"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="model-context">Context length</Label>
              <Input
                id="model-context"
                type="number"
                value={contextLength}
                onChange={(e) => setContextLength(e.target.value)}
                placeholder="32768"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="model-license">License</Label>
              <Input
                id="model-license"
                value={license}
                onChange={(e) => setLicense(e.target.value)}
                placeholder="apache-2.0"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="model-quantization">Quantization</Label>
              <Input
                id="model-quantization"
                value={quantization}
                onChange={(e) => setQuantization(e.target.value)}
                placeholder="none / awq / gguf-q4"
              />
            </div>

            <div className="col-span-2 flex flex-col gap-1.5">
              <Label htmlFor="model-local-path">Local path (optional)</Label>
              <Input
                id="model-local-path"
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
                placeholder="/data/models/qwen2.5-7b"
              />
            </div>

            {error ? (
              <p className="col-span-2 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            ) : null}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
              Register
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
