"""LLaMA-Factory training provider adapter.

Translates our provider-agnostic hom_core.schemas.training.TrainingConfig
into a LLaMA-Factory YAML config + dataset_info.json registration, and
drives `llamafactory-cli train` as a subprocess. This is the *only* file
in the whole platform that knows LLaMA-Factory's config format or CLI -
everything above (tasks.py, apps/api) only ever talks to the
TrainingProvider interface.

Swapping to a different trainer (Axolotl, an in-house one) means writing
a new class implementing hom_core.providers.TrainingProvider - nothing
else changes.
"""

import json
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path

from hom_core.enums import ErrorCode, TrainingJobStatus, TrainingType
from hom_core.providers.training_provider import TrainingProvider, TrainingStatusUpdate
from hom_core.schemas.training import (
    TrainingArtifacts,
    TrainingConfig,
    TrainingJobError,
    TrainingLogLine,
    TrainingMetricsSnapshot,
)

_TRAINING_TYPE_TO_FINETUNING = {
    TrainingType.LORA: "lora",
    TrainingType.QLORA: "lora",  # QLoRA = LoRA + quantization_bit
    TrainingType.FULL: "full",
    TrainingType.SFT: "lora",
    TrainingType.DPO: "lora",
}

_TRAINING_TYPE_TO_STAGE = {
    TrainingType.DPO: "dpo",
}


class LlamaFactoryNotInstalled(RuntimeError):
    pass


class TrainingProcessError(RuntimeError):
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.PROVIDER_ERROR):
        super().__init__(message)
        self.error_code = error_code


@dataclass
class _RunHandle:
    run_dir: Path
    config_path: Path
    output_dir: Path
    pid_file: Path
    stdout_log: Path


class LlamaFactoryTrainingProvider(TrainingProvider):
    def __init__(self, repo_path: str, work_dir: str, python_executable: str = "python"):
        self.repo_path = Path(repo_path)
        self.work_dir = Path(work_dir)
        self.python_executable = python_executable
        self.work_dir.mkdir(parents=True, exist_ok=True)

    # -- helpers -----------------------------------------------------

    def _run_dir(self, job_id: str) -> Path:
        d = self.work_dir / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _cli_available(self) -> bool:
        return shutil.which("llamafactory-cli") is not None

    def _build_config_dict(self, config: TrainingConfig, dataset_name: str) -> dict:
        hp = config.hyperparameters
        finetuning_type = _TRAINING_TYPE_TO_FINETUNING[config.training_type]
        stage = _TRAINING_TYPE_TO_STAGE.get(config.training_type, "sft")

        cfg: dict = {
            "stage": stage,
            "do_train": True,
            "model_name_or_path": config.base_model_local_path or config.base_model_huggingface_id,
            "dataset": dataset_name,
            "dataset_dir": str(self._run_dir(config.job_id)),
            "template": "default",
            "finetuning_type": finetuning_type,
            "output_dir": config.output_dir,
            "overwrite_output_dir": True,
            "per_device_train_batch_size": hp.batch_size,
            "gradient_accumulation_steps": hp.gradient_accumulation_steps,
            "learning_rate": hp.learning_rate,
            "num_train_epochs": hp.epochs,
            "lr_scheduler_type": "cosine",
            "warmup_ratio": hp.warmup_ratio,
            "weight_decay": hp.weight_decay,
            "cutoff_len": hp.context_length,
            "bf16": hp.bf16,
            "fp16": hp.fp16,
            "gradient_checkpointing": hp.gradient_checkpointing,
            "logging_steps": 10,
            "save_steps": 200,
            "plot_loss": True,
            "seed": config.seed,
        }

        if finetuning_type == "lora":
            cfg["lora_rank"] = hp.lora_rank
            cfg["lora_alpha"] = hp.lora_alpha
            cfg["lora_dropout"] = hp.lora_dropout
            cfg["lora_target"] = "all"

        if config.training_type == TrainingType.QLORA:
            cfg["quantization_bit"] = 4

        cfg.update(config.extra)
        return cfg

    def _write_yaml(self, path: Path, data: dict) -> None:
        # Minimal, dependency-free YAML writer (flat key: value + JSON for
        # nested values) - avoids requiring PyYAML just for this.
        lines = []
        for key, value in data.items():
            if isinstance(value, bool):
                rendered = "true" if value else "false"
            elif isinstance(value, str):
                rendered = json.dumps(value)
            else:
                rendered = json.dumps(value)
            lines.append(f"{key}: {rendered}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _register_dataset(self, run_dir: Path, dataset_name: str, dataset_local_path: str, dataset_format: str) -> None:
        formatting = "sharegpt" if dataset_format in ("json", "jsonl") else "alpaca"
        dataset_info = {
            dataset_name: {
                "file_name": dataset_local_path,
                "formatting": formatting,
                "columns": {"messages": "messages"},
            }
        }
        (run_dir / "dataset_info.json").write_text(json.dumps(dataset_info, indent=2), encoding="utf-8")

    # -- TrainingProvider interface -----------------------------------

    def prepare_training(self, config: TrainingConfig) -> str:
        run_dir = self._run_dir(config.job_id)
        dataset_name = f"job-{config.job_id}"

        self._register_dataset(run_dir, dataset_name, config.dataset_path, config.dataset_format)

        cfg_dict = self._build_config_dict(config, dataset_name)
        config_path = run_dir / "train_config.yaml"
        self._write_yaml(config_path, cfg_dict)

        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        return str(config_path)

    def start_training(self, config: TrainingConfig, prepared_handle: str) -> str:
        if not self._cli_available():
            raise LlamaFactoryNotInstalled(
                "llamafactory-cli was not found on PATH. Install LLaMA-Factory in the "
                "training-worker image/environment to run real training jobs."
            )

        run_dir = self._run_dir(config.job_id)
        stdout_log = run_dir / "stdout.log"
        pid_file = run_dir / "run.pid"

        with open(stdout_log, "ab") as log_f:
            process = subprocess.Popen(
                ["llamafactory-cli", "train", prepared_handle],
                cwd=str(self.repo_path) if self.repo_path.exists() else None,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                shell=False,
                start_new_session=True,  # own process group, so we can kill children on cancel
            )
        pid_file.write_text(str(process.pid), encoding="utf-8")
        return config.job_id

    def _handle(self, run_id: str) -> _RunHandle:
        run_dir = self._run_dir(run_id)
        return _RunHandle(
            run_dir=run_dir,
            config_path=run_dir / "train_config.yaml",
            output_dir=run_dir,  # actual output_dir is inside the config; trainer_state.json path is resolved below
            pid_file=run_dir / "run.pid",
            stdout_log=run_dir / "stdout.log",
        )

    def _is_process_alive(self, pid_file: Path) -> bool:
        if not pid_file.exists():
            return False
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError, PermissionError):
            return False

    def _read_new_log_lines(self, stdout_log: Path, offset: int = 0) -> list[str]:
        if not stdout_log.exists():
            return []
        with open(stdout_log, "r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            return f.readlines()

    def get_status(self, run_id: str) -> TrainingStatusUpdate:
        handle = self._handle(run_id)
        alive = self._is_process_alive(handle.pid_file)

        logs = [
            TrainingLogLine(timestamp=_now(), message=line.rstrip("\n"))
            for line in self._read_new_log_lines(handle.stdout_log)
            if line.strip()
        ][-50:]

        metrics = self._read_trainer_state_metrics(handle)

        if alive:
            status = TrainingJobStatus.RUNNING
        elif self._trainer_state_indicates_success(handle):
            status = TrainingJobStatus.COMPLETED
        else:
            status = TrainingJobStatus.FAILED

        error = None
        if status == TrainingJobStatus.FAILED:
            error = TrainingJobError(
                error_code=ErrorCode.PROVIDER_ERROR,
                message="Training process exited without producing a completed trainer_state.json.",
                failed_step="training",
                suggested_actions=[
                    "Check the training logs for a stack trace",
                    "Verify the base model and dataset paths are reachable from the worker container",
                ],
            )

        return TrainingStatusUpdate(status=status, logs=logs, metrics=metrics, error=error)

    def _trainer_state_path(self, handle: _RunHandle) -> Path | None:
        candidates = list(handle.run_dir.glob("**/trainer_state.json"))
        return candidates[0] if candidates else None

    def _read_trainer_state_metrics(self, handle: _RunHandle) -> TrainingMetricsSnapshot | None:
        path = self._trainer_state_path(handle)
        if path is None or not path.exists():
            return None
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        log_history = state.get("log_history") or []
        if not log_history:
            return None
        last = log_history[-1]
        return TrainingMetricsSnapshot(
            timestamp=_now(),
            epoch=last.get("epoch", 0.0),
            step=state.get("global_step", 0),
            total_steps=state.get("max_steps"),
            loss=last.get("loss"),
            learning_rate=last.get("learning_rate"),
        )

    def _trainer_state_indicates_success(self, handle: _RunHandle) -> bool:
        path = self._trainer_state_path(handle)
        if path is None:
            return False
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        return bool(state.get("log_history"))

    def cancel_training(self, run_id: str) -> None:
        handle = self._handle(run_id)
        if not handle.pid_file.exists():
            return
        try:
            pid = int(handle.pid_file.read_text().strip())
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ValueError, ProcessLookupError, PermissionError, OSError):
            pass

    def get_artifacts(self, run_id: str) -> TrainingArtifacts:
        handle = self._handle(run_id)
        checkpoints = sorted(str(p) for p in handle.run_dir.glob("**/checkpoint-*"))
        adapter_candidates = list(handle.run_dir.glob("**/adapter_model.safetensors"))
        final_loss = None
        state_path = self._trainer_state_path(handle)
        if state_path and state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                history = state.get("log_history") or []
                if history:
                    final_loss = history[-1].get("loss")
            except (json.JSONDecodeError, OSError):
                pass

        return TrainingArtifacts(
            output_dir=str(handle.run_dir),
            adapter_path=str(adapter_candidates[0].parent) if adapter_candidates else None,
            checkpoint_paths=checkpoints,
            final_loss=final_loss,
        )


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
