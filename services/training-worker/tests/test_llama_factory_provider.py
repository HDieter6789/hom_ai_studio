import json
from pathlib import Path

import pytest

from hom_core.enums import TrainingPreset, TrainingType
from hom_core.schemas.training import HyperParameters, TrainingConfig
from worker.providers.llama_factory import LlamaFactoryTrainingProvider


@pytest.fixture
def provider(tmp_path):
    return LlamaFactoryTrainingProvider(repo_path=str(tmp_path / "repo"), work_dir=str(tmp_path / "runs"))


def _config(**overrides) -> TrainingConfig:
    defaults = dict(
        job_id="job-1",
        training_name="CRM-Core-test",
        base_model_id="model-1",
        base_model_local_path="/models/qwen2.5-7b",
        base_model_huggingface_id=None,
        dataset_id="dataset-1",
        dataset_path="/data/storage/datasets/dataset-1/source.jsonl",
        dataset_format="jsonl",
        training_type=TrainingType.QLORA,
        preset=TrainingPreset.BALANCED,
        hyperparameters=HyperParameters(),
        output_dir="/data/storage/artifacts/job-1",
    )
    defaults.update(overrides)
    return TrainingConfig(**defaults)


def test_prepare_training_writes_config_and_dataset_registration(provider, tmp_path):
    config = _config()

    config_path = provider.prepare_training(config)

    assert Path(config_path).exists()
    content = Path(config_path).read_text(encoding="utf-8")
    assert "model_name_or_path" in content
    assert "lora_rank" in content  # QLoRA still uses the LoRA config surface
    assert "quantization_bit" in content  # ...plus 4-bit quantization

    dataset_info_path = Path(provider._run_dir(config.job_id)) / "dataset_info.json"
    assert dataset_info_path.exists()
    registered = json.loads(dataset_info_path.read_text(encoding="utf-8"))
    assert config.dataset_path in json.dumps(registered)


def test_full_fine_tuning_does_not_add_lora_keys(provider):
    config = _config(training_type=TrainingType.FULL)

    config_path = provider.prepare_training(config)
    content = Path(config_path).read_text(encoding="utf-8")

    assert "lora_rank" not in content
    assert "quantization_bit" not in content


def test_starting_without_llamafactory_cli_raises_clear_error(provider, monkeypatch):
    from worker.providers.llama_factory import LlamaFactoryNotInstalled

    monkeypatch.setattr(provider, "_cli_available", lambda: False)
    config = _config()
    handle = provider.prepare_training(config)

    with pytest.raises(LlamaFactoryNotInstalled):
        provider.start_training(config, handle)


def test_get_status_without_any_run_reports_failed(provider):
    config = _config()
    provider.prepare_training(config)
    # No process was ever started - no pid file, no trainer_state.json.
    update = provider.get_status(config.job_id)

    assert update.status.value == "failed"
    assert update.error is not None


def test_get_artifacts_reports_empty_before_training_runs(provider):
    config = _config()
    provider.prepare_training(config)

    artifacts = provider.get_artifacts(config.job_id)

    assert artifacts.checkpoint_paths == []
    assert artifacts.adapter_path is None
