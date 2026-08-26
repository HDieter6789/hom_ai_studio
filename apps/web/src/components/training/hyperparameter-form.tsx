import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import type { TrainingHyperparameters } from "@/lib/types";

interface HyperparameterFormProps {
  values: TrainingHyperparameters;
  editable: boolean;
  onChange: (values: TrainingHyperparameters) => void;
}

interface FieldDef {
  key: keyof TrainingHyperparameters;
  label: string;
  step?: string;
  kind: "number" | "boolean";
}

const NUMERIC_FIELDS: FieldDef[] = [
  { key: "epochs", label: "Epochs", kind: "number", step: "1" },
  { key: "learning_rate", label: "Learning rate", kind: "number", step: "0.00001" },
  { key: "batch_size", label: "Batch size", kind: "number", step: "1" },
  {
    key: "gradient_accumulation_steps",
    label: "Grad. accumulation steps",
    kind: "number",
    step: "1",
  },
  { key: "context_length", label: "Context length", kind: "number", step: "1" },
  { key: "warmup_ratio", label: "Warmup ratio", kind: "number", step: "0.01" },
  { key: "weight_decay", label: "Weight decay", kind: "number", step: "0.01" },
  { key: "lora_rank", label: "LoRA rank", kind: "number", step: "1" },
  { key: "lora_alpha", label: "LoRA alpha", kind: "number", step: "1" },
  { key: "lora_dropout", label: "LoRA dropout", kind: "number", step: "0.01" },
];

const BOOLEAN_FIELDS: FieldDef[] = [
  { key: "bf16", label: "BF16 precision", kind: "boolean" },
  { key: "fp16", label: "FP16 precision", kind: "boolean" },
  { key: "gradient_checkpointing", label: "Gradient checkpointing", kind: "boolean" },
];

export function HyperparameterForm({ values, editable, onChange }: HyperparameterFormProps) {
  function setField<K extends keyof TrainingHyperparameters>(
    key: K,
    value: TrainingHyperparameters[K],
  ) {
    onChange({ ...values, [key]: value });
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {NUMERIC_FIELDS.map((field) => (
          <div key={field.key} className="flex flex-col gap-1.5">
            <Label htmlFor={`hp-${field.key}`}>{field.label}</Label>
            <Input
              id={`hp-${field.key}`}
              type="number"
              step={field.step}
              disabled={!editable}
              value={values[field.key] === null || values[field.key] === undefined ? "" : String(values[field.key])}
              onChange={(e) =>
                setField(
                  field.key,
                  e.target.value === "" ? null : Number(e.target.value),
                )
              }
              className="tabular-nums disabled:opacity-100"
            />
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-6">
        {BOOLEAN_FIELDS.map((field) => (
          <div key={field.key} className="flex items-center gap-2.5">
            <Switch
              id={`hp-${field.key}`}
              disabled={!editable}
              checked={Boolean(values[field.key])}
              onCheckedChange={(checked) => setField(field.key, checked)}
            />
            <Label htmlFor={`hp-${field.key}`} className="font-normal">
              {field.label}
            </Label>
          </div>
        ))}
      </div>
    </div>
  );
}
