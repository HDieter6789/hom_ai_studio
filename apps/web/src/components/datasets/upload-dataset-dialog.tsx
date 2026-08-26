"use client";

import * as React from "react";
import { Loader2, Upload } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError, uploadDataset } from "@/lib/api";
import { DATASET_TYPE_LABELS } from "@/lib/status";
import type { DatasetOut, DatasetType } from "@/lib/types";
import { toast } from "sonner";

interface UploadDatasetDialogProps {
  onUploaded?: (dataset: DatasetOut) => void;
}

const DATASET_TYPES = Object.keys(DATASET_TYPE_LABELS) as DatasetType[];

export function UploadDatasetDialog({ onUploaded }: UploadDatasetDialogProps) {
  const [open, setOpen] = React.useState(false);
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [type, setType] = React.useState<DatasetType>("instruction");
  const [file, setFile] = React.useState<File | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  function reset() {
    setName("");
    setDescription("");
    setType("instruction");
    setFile(null);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Please choose a file to upload.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const dataset = await uploadDataset({ name, description, type, file });
      toast.success(`Dataset "${dataset.name}" uploaded`);
      onUploaded?.(dataset);
      setOpen(false);
      reset();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to upload dataset.",
      );
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
          <Upload className="size-4" />
          Upload dataset
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Upload dataset</DialogTitle>
            <DialogDescription>
              Upload a .json, .jsonl or .csv file. It will be validated and
              profiled automatically after upload.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dataset-name">Name</Label>
              <Input
                id="dataset-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="crm-support-tickets-v2"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dataset-description">Description (optional)</Label>
              <Textarea
                id="dataset-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What's in this dataset?"
                rows={2}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dataset-type">Type</Label>
              <Select value={type} onValueChange={(v) => setType(v as DatasetType)}>
                <SelectTrigger id="dataset-type" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DATASET_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {DATASET_TYPE_LABELS[t]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dataset-file">File</Label>
              <Input
                id="dataset-file"
                type="file"
                accept=".json,.jsonl,.csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                required
              />
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
            <Button type="submit" disabled={submitting}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
              Upload
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
