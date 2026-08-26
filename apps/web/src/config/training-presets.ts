import type { TrainingHyperparameters, TrainingPreset, TrainingType } from "@/lib/types";

// Client-side display defaults for each preset. These are only used to show
// sensible read-only values in the training wizard and, for the "custom"
// preset, as an editable starting point sent as `hyperparameter_overrides`.
// The backend owns the real defaults for "fast"/"balanced"/"high_quality" —
// we never send hyperparameters for those presets, only `preset` itself.
export const PRESET_HYPERPARAMETERS: Record<
  Exclude<TrainingPreset, "custom">,
  TrainingHyperparameters
> = {
  fast: {
    epochs: 1,
    learning_rate: 0.0002,
    batch_size: 8,
    gradient_accumulation_steps: 1,
    context_length: 2048,
    warmup_ratio: 0.03,
    weight_decay: 0,
    lora_rank: 8,
    lora_alpha: 16,
    lora_dropout: 0.05,
    bf16: true,
    fp16: false,
    gradient_checkpointing: true,
  },
  balanced: {
    epochs: 3,
    learning_rate: 0.0001,
    batch_size: 4,
    gradient_accumulation_steps: 4,
    context_length: 4096,
    warmup_ratio: 0.05,
    weight_decay: 0.01,
    lora_rank: 16,
    lora_alpha: 32,
    lora_dropout: 0.05,
    bf16: true,
    fp16: false,
    gradient_checkpointing: true,
  },
  high_quality: {
    epochs: 5,
    learning_rate: 0.00005,
    batch_size: 2,
    gradient_accumulation_steps: 8,
    context_length: 8192,
    warmup_ratio: 0.1,
    weight_decay: 0.01,
    lora_rank: 32,
    lora_alpha: 64,
    lora_dropout: 0.1,
    bf16: true,
    fp16: false,
    gradient_checkpointing: true,
  },
};

export const CUSTOM_DEFAULT_HYPERPARAMETERS: TrainingHyperparameters =
  PRESET_HYPERPARAMETERS.balanced;

export interface PresetInfo {
  value: TrainingPreset;
  title: string;
  description: string;
  badge: string;
}

export const TRAINING_PRESETS: PresetInfo[] = [
  {
    value: "fast",
    title: "Fast",
    description: "Quick iteration — fewer epochs, larger batches, shorter context.",
    badge: "~30 min",
  },
  {
    value: "balanced",
    title: "Balanced",
    description: "Good default for most CRM fine-tuning runs.",
    badge: "Recommended",
  },
  {
    value: "high_quality",
    title: "High Quality",
    description: "More epochs and higher rank LoRA for best results.",
    badge: "Slower",
  },
  {
    value: "custom",
    title: "Custom",
    description: "Pick the training type and tune every hyperparameter yourself.",
    badge: "Advanced",
  },
];

export const TRAINING_TYPES: { value: TrainingType; label: string }[] = [
  { value: "lora", label: "LoRA" },
  { value: "qlora", label: "QLoRA" },
  { value: "full_fine_tuning", label: "Full Fine-tuning" },
  { value: "sft", label: "SFT" },
  { value: "dpo", label: "DPO" },
];
