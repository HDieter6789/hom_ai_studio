"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { InlineError } from "@/components/shared/inline-error";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PresetCard } from "@/components/training/preset-card";
import { HyperparameterForm } from "@/components/training/hyperparameter-form";
import { useBaseModels } from "@/hooks/use-models";
import { useDatasets } from "@/hooks/use-datasets";
import { createTrainingJob } from "@/hooks/use-training";
import { ApiError } from "@/lib/api";
import {
  CUSTOM_DEFAULT_HYPERPARAMETERS,
  PRESET_HYPERPARAMETERS,
  TRAINING_PRESETS,
  TRAINING_TYPES,
} from "@/config/training-presets";
import type {
  TrainingHyperparameters,
  TrainingPreset,
  TrainingType,
} from "@/lib/types";
import { cn } from "@/lib/utils";

export default function NewTrainingRunPage() {
  const router = useRouter();
  const { data: baseModels, error: baseModelsError } = useBaseModels();
  const { data: datasets, error: datasetsError } = useDatasets();

  const [step, setStep] = React.useState<1 | 2>(1);
  const [name, setName] = React.useState("");
  const [baseModelId, setBaseModelId] = React.useState("");
  const [datasetId, setDatasetId] = React.useState("");
  const [preset, setPreset] = React.useState<TrainingPreset>("balanced");
  const [trainingType, setTrainingType] = React.useState<TrainingType>("lora");
  const [hyperparameters, setHyperparameters] = React.useState<TrainingHyperparameters>(
    PRESET_HYPERPARAMETERS.balanced,
  );
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  function handlePresetChange(next: TrainingPreset) {
    setPreset(next);
    setHyperparameters(
      next === "custom" ? CUSTOM_DEFAULT_HYPERPARAMETERS : PRESET_HYPERPARAMETERS[next],
    );
  }

  const step1Valid = Boolean(name.trim() && baseModelId && datasetId);

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const job = await createTrainingJob({
        name,
        base_model_id: baseModelId,
        dataset_id: datasetId,
        preset,
        ...(preset === "custom"
          ? {
              training_type: trainingType,
              hyperparameter_overrides: hyperparameters as unknown as Record<string, unknown>,
            }
          : {}),
      });
      toast.success(`Training run "${job.name}" started`);
      router.push(`/training/${job.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start training run.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Button variant="ghost" size="sm" className="mb-3 -ml-2" onClick={() => router.push("/training")}>
          <ArrowLeft className="size-4" />
          Back to training
        </Button>
        <PageHeader
          title="New training run"
          description="Configure a fine-tuning job for the HOM-CRM model family."
        />
      </div>

      <div className="flex items-center gap-3 text-sm">
        <StepPill index={1} label="Setup" active={step === 1} done={step > 1} />
        <div className="h-px w-8 bg-border" />
        <StepPill index={2} label="Hyperparameters" active={step === 2} done={false} />
      </div>

      {baseModelsError || datasetsError ? (
        <InlineError message={baseModelsError || datasetsError || "Failed to load"} />
      ) : null}

      {step === 1 ? (
        <Card>
          <CardContent className="flex flex-col gap-6">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="run-name">Run name</Label>
              <Input
                id="run-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="hom-crm-tool-calling-v4"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="base-model">Base model</Label>
                <Select value={baseModelId} onValueChange={setBaseModelId}>
                  <SelectTrigger id="base-model" className="w-full">
                    <SelectValue placeholder="Select a base model" />
                  </SelectTrigger>
                  <SelectContent>
                    {(baseModels ?? []).map((m) => (
                      <SelectItem key={m.id} value={m.id}>
                        {m.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {baseModels && baseModels.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    No base models yet — register one under Models first.
                  </p>
                ) : null}
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dataset">Dataset</Label>
                <Select value={datasetId} onValueChange={setDatasetId}>
                  <SelectTrigger id="dataset" className="w-full">
                    <SelectValue placeholder="Select a dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    {(datasets ?? []).map((d) => (
                      <SelectItem key={d.id} value={d.id}>
                        {d.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {datasets && datasets.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    No datasets yet — upload one under Datasets first.
                  </p>
                ) : null}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <Label>Training preset</Label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {TRAINING_PRESETS.map((p) => (
                  <PresetCard
                    key={p.value}
                    preset={p}
                    selected={preset === p.value}
                    onSelect={() => handlePresetChange(p.value)}
                  />
                ))}
              </div>
            </div>

            {preset === "custom" ? (
              <div className="flex flex-col gap-1.5 sm:w-64">
                <Label htmlFor="training-type">Training type</Label>
                <Select value={trainingType} onValueChange={(v) => setTrainingType(v as TrainingType)}>
                  <SelectTrigger id="training-type" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRAINING_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}

            <div className="flex justify-end">
              <Button onClick={() => setStep(2)} disabled={!step1Valid}>
                Next: Hyperparameters
                <ArrowRight className="size-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="flex flex-col gap-6">
            <div>
              <h3 className="text-sm font-medium">
                {preset === "custom" ? "Custom hyperparameters" : "Preset hyperparameters"}
              </h3>
              <p className="mt-1 text-xs text-muted-foreground">
                {preset === "custom"
                  ? "These values are sent as hyperparameter_overrides."
                  : "Shown for reference — the backend applies its own defaults for this preset."}
              </p>
            </div>

            <HyperparameterForm
              values={hyperparameters}
              editable={preset === "custom"}
              onChange={setHyperparameters}
            />

            {error ? (
              <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            ) : null}

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ArrowLeft className="size-4" />
                Back
              </Button>
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
                Start training run
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StepPill({
  index,
  label,
  active,
  done,
}: {
  index: number;
  label: string;
  active: boolean;
  done: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          "flex size-5 items-center justify-center rounded-full text-xs font-medium",
          active || done
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground",
        )}
      >
        {index}
      </span>
      <span className={cn("font-medium", active ? "text-foreground" : "text-muted-foreground")}>
        {label}
      </span>
    </div>
  );
}
