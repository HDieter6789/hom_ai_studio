import pytest
from fastapi import HTTPException

from app.services.training_config import build_hyperparameters, resolve_training_type
from hom_core.enums import TrainingPreset, TrainingType
from hom_core.schemas.training import resolve_hyperparameters


def test_balanced_preset_matches_product_spec_defaults():
    hp = resolve_hyperparameters(TrainingPreset.BALANCED)

    assert hp.epochs == 3
    assert hp.learning_rate == 2e-5
    assert hp.lora_rank == 32
    assert hp.gradient_checkpointing is True


def test_fast_preset_is_cheaper_than_high_quality():
    fast = resolve_hyperparameters(TrainingPreset.FAST)
    high_quality = resolve_hyperparameters(TrainingPreset.HIGH_QUALITY)

    assert fast.epochs <= high_quality.epochs
    assert fast.context_length <= high_quality.context_length
    assert fast.lora_rank <= high_quality.lora_rank


def test_overrides_win_over_preset_defaults():
    hp = build_hyperparameters(TrainingPreset.BALANCED, {"epochs": 7})

    assert hp.epochs == 7
    assert hp.lora_rank == 32  # untouched fields keep the preset value


def test_bf16_and_fp16_are_mutually_exclusive():
    with pytest.raises(HTTPException) as exc_info:
        build_hyperparameters(TrainingPreset.CUSTOM, {"bf16": True, "fp16": True})

    assert exc_info.value.status_code == 400


def test_custom_preset_requires_explicit_training_type():
    with pytest.raises(HTTPException) as exc_info:
        resolve_training_type(TrainingPreset.CUSTOM, None)

    assert exc_info.value.status_code == 400


def test_non_custom_preset_ignores_requested_training_type():
    resolved = resolve_training_type(TrainingPreset.FAST, None)

    assert resolved == TrainingType.QLORA
