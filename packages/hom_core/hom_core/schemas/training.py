from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from hom_core.enums import ErrorCode, TrainingPreset, TrainingType


class HyperParameters(BaseModel):
    """Training hyperparameters. Every field has a safe default so a user
    can start from a preset and only override what they care about."""

    epochs: float = Field(default=3, gt=0, le=100)
    learning_rate: float = Field(default=2e-5, gt=0, le=1e-2)
    batch_size: int = Field(default=4, ge=1, le=1024)
    gradient_accumulation_steps: int = Field(default=8, ge=1, le=256)
    context_length: int = Field(default=4096, ge=128, le=131072)
    warmup_ratio: float = Field(default=0.03, ge=0, le=1)
    weight_decay: float = Field(default=0.01, ge=0, le=1)
    lora_rank: int = Field(default=32, ge=1, le=1024)
    lora_alpha: int = Field(default=64, ge=1, le=2048)
    lora_dropout: float = Field(default=0.05, ge=0, le=1)
    bf16: bool = True
    fp16: bool = False
    gradient_checkpointing: bool = True

    @model_validator(mode="after")
    def _mutually_exclusive_precision(self) -> "HyperParameters":
        if self.bf16 and self.fp16:
            raise ValueError("bf16 and fp16 are mutually exclusive")
        return self


PRESET_HYPERPARAMETERS: dict[TrainingPreset, dict[str, Any]] = {
    TrainingPreset.FAST: dict(
        epochs=1,
        learning_rate=3e-5,
        batch_size=8,
        gradient_accumulation_steps=4,
        context_length=2048,
        lora_rank=16,
        lora_alpha=32,
        gradient_checkpointing=True,
    ),
    TrainingPreset.BALANCED: dict(
        epochs=3,
        learning_rate=2e-5,
        batch_size=4,
        gradient_accumulation_steps=8,
        context_length=4096,
        lora_rank=32,
        lora_alpha=64,
        gradient_checkpointing=True,
    ),
    TrainingPreset.HIGH_QUALITY: dict(
        epochs=5,
        learning_rate=1e-5,
        batch_size=2,
        gradient_accumulation_steps=16,
        context_length=8192,
        lora_rank=64,
        lora_alpha=128,
        gradient_checkpointing=True,
    ),
}

# Preset -> recommended training type. HIGH_QUALITY still defaults to QLoRA
# to keep hardware requirements realistic; users who want full fine-tuning
# choose Custom explicitly.
PRESET_TRAINING_TYPE: dict[TrainingPreset, TrainingType] = {
    TrainingPreset.FAST: TrainingType.QLORA,
    TrainingPreset.BALANCED: TrainingType.QLORA,
    TrainingPreset.HIGH_QUALITY: TrainingType.LORA,
}


def resolve_hyperparameters(
    preset: TrainingPreset, overrides: dict[str, Any] | None = None
) -> HyperParameters:
    """Build HyperParameters from a preset, optionally overridden by
    explicit user values (used when preset == CUSTOM, or when a user
    tweaks a single field on top of a preset)."""
    base = dict(PRESET_HYPERPARAMETERS.get(preset, {}))
    if overrides:
        base.update({k: v for k, v in overrides.items() if v is not None})
    return HyperParameters(**base)


class TrainingConfig(BaseModel):
    """Provider-agnostic training configuration. This is what
    TrainingProvider.prepare_training() receives - it knows nothing about
    LLaMA-Factory or any other concrete trainer."""

    job_id: str
    training_name: str
    base_model_id: str
    base_model_local_path: str | None = None
    base_model_huggingface_id: str | None = None
    dataset_id: str
    dataset_path: str
    dataset_format: Literal["json", "jsonl", "csv"]
    training_type: TrainingType
    preset: TrainingPreset
    hyperparameters: HyperParameters
    output_dir: str
    seed: int = 42
    extra: dict[str, Any] = Field(default_factory=dict)


class TrainingLogLine(BaseModel):
    timestamp: datetime
    level: Literal["debug", "info", "warning", "error"] = "info"
    message: str


class TrainingMetricsSnapshot(BaseModel):
    timestamp: datetime
    epoch: float
    step: int
    total_steps: int | None = None
    loss: float | None = None
    learning_rate: float | None = None
    gpu_memory_used_gb: float | None = None
    gpu_utilization_pct: float | None = None
    samples_per_sec: float | None = None
    tokens_per_sec: float | None = None


class TrainingJobError(BaseModel):
    error_code: ErrorCode
    message: str
    failed_step: str | None = None
    suggested_actions: list[str] = Field(default_factory=list)
    gpu_context: str | None = None


class TrainingArtifacts(BaseModel):
    output_dir: str
    adapter_path: str | None = None
    merged_model_path: str | None = None
    checkpoint_paths: list[str] = Field(default_factory=list)
    final_loss: float | None = None
