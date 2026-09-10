"""Remote LLaMA-Factory training provider.

Implements the same hom_core.providers.TrainingProvider interface as
LlamaFactoryTrainingProvider, but instead of running `llamafactory-cli`
as a local subprocess, it delegates the actual training run to a small
HTTP agent running on a remote GPU box (e.g. a Google Colab notebook
with a T4 GPU). The VPS worker never runs training itself in this mode -
it only uploads the dataset + config and polls status/logs.

Talks to these endpoints on the remote agent:
  GET  /gpus                          - used by RemoteGPUProvider (compute_remote.py), not here
  POST /jobs                          - {job_id, config: dict, dataset: base64} -> {run_id}
  GET  /jobs/{run_id}/status          -> {status, logs: [...], metrics: {...} | null, error: {...} | null}
  POST /jobs/{run_id}/cancel          -> {ok: true}
  GET  /jobs/{run_id}/artifacts       -> {output_dir, adapter_path, checkpoint_paths, final_loss}

All requests carry `X-Agent-Token` for auth - the agent rejects anything
without the matching shared token.
"""

import base64
import json
from datetime import datetime, timezone

import httpx

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
    TrainingType.QLORA: "lora",
    TrainingType.FULL: "full",
    TrainingType.SFT: "lora",
    TrainingType.DPO: "lora",
}
_TRAINING_TYPE_TO_STAGE = {TrainingType.DPO: "dpo"}


class RemoteAgentUnreachable(RuntimeError):
    pass


class LlamaFactoryRemoteProvider(TrainingProvider):
    def __init__(self, agent_url: str, agent_token: str, timeout_seconds: float = 30.0):
        self.agent_url = agent_url.rstrip("/")
        self.agent_token = agent_token
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict:
        return {"X-Agent-Token": self.agent_token}

    def _build_config_dict(self, config: TrainingConfig, dataset_name: str) -> dict:
        hp = config.hyperparameters
        finetuning_type = _TRAINING_TYPE_TO_FINETUNING[config.training_type]
        stage = _TRAINING_TYPE_TO_STAGE.get(config.training_type, "sft")
        cfg: dict = {
            "stage": stage,
            "do_train": True,
            "model_name_or_path": config.base_model_local_path or config.base_model_huggingface_id,
            "dataset": dataset_name,
            "template": "default",
            "finetuning_type": finetuning_type,
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

    # -- TrainingProvider interface -----------------------------------

    def prepare_training(self, config: TrainingConfig) -> str:
        # Nothing to materialize locally - config + dataset are sent together
        # in start_training(). We just hand back a JSON-encoded handle.
        dataset_name = f"job-{config.job_id}"
        cfg_dict = self._build_config_dict(config, dataset_name)
        return json.dumps({"dataset_name": dataset_name, "config": cfg_dict})

    def start_training(self, config: TrainingConfig, prepared_handle: str) -> str:
        handle = json.loads(prepared_handle)
        try:
            with open(config.dataset_path, "rb") as f:
                dataset_b64 = base64.b64encode(f.read()).decode("ascii")
        except OSError as exc:
            raise RemoteAgentUnreachable(f"Could not read dataset at {config.dataset_path}: {exc}") from exc

        payload = {
            "job_id": config.job_id,
            "dataset_format": config.dataset_format,
            "dataset_b64": dataset_b64,
            "config": handle["config"],
        }
        try:
            resp = httpx.post(f"{self.agent_url}/jobs", json=payload, headers=self._headers(), timeout=self.timeout_seconds)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise RemoteAgentUnreachable(f"Colab agent unreachable or rejected job: {exc}") from exc
        return resp.json()["run_id"]

    def get_status(self, run_id: str) -> TrainingStatusUpdate:
        try:
            resp = httpx.get(f"{self.agent_url}/jobs/{run_id}/status", headers=self._headers(), timeout=self.timeout_seconds)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            # Agent unreachable (Colab session died, ToS-Kick, etc.) - report
            # as a failed job with a clear reason rather than hanging forever.
            return TrainingStatusUpdate(
                status=TrainingJobStatus.FAILED,
                error=TrainingJobError(
                    error_code=ErrorCode.PROVIDER_ERROR,
                    message=f"Colab agent unreachable: {exc}",
                    failed_step="remote_status_poll",
                    suggested_actions=[
                        "Pruefen ob die Colab-Session noch laeuft (Browser-Tab, Remote-Tunnel)",
                        "UptimeRobot-Monitor-Status pruefen",
                    ],
                ),
            )
        data = resp.json()
        logs = [TrainingLogLine(timestamp=datetime.now(timezone.utc), level=l.get("level", "info"), message=l["message"]) for l in data.get("logs", [])]
        metrics = None
        if data.get("metrics"):
            m = data["metrics"]
            metrics = TrainingMetricsSnapshot(
                timestamp=datetime.now(timezone.utc),
                epoch=m.get("epoch", 0.0),
                step=m.get("step", 0),
                total_steps=m.get("total_steps"),
                loss=m.get("loss"),
                learning_rate=m.get("learning_rate"),
            )
        error = None
        if data.get("error"):
            e = data["error"]
            error = TrainingJobError(
                error_code=ErrorCode(e.get("error_code", ErrorCode.PROVIDER_ERROR.value)),
                message=e.get("message", "Unknown remote error"),
                failed_step=e.get("failed_step"),
                suggested_actions=e.get("suggested_actions", []),
            )
        return TrainingStatusUpdate(status=TrainingJobStatus(data["status"]), logs=logs, metrics=metrics, error=error)

    def cancel_training(self, run_id: str) -> None:
        try:
            httpx.post(f"{self.agent_url}/jobs/{run_id}/cancel", headers=self._headers(), timeout=self.timeout_seconds)
        except httpx.HTTPError:
            pass  # best-effort, same contract as the local provider

    def get_artifacts(self, run_id: str) -> TrainingArtifacts:
        resp = httpx.get(f"{self.agent_url}/jobs/{run_id}/artifacts", headers=self._headers(), timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        return TrainingArtifacts(
            output_dir=data.get("output_dir", ""),
            adapter_path=data.get("adapter_path"),
            checkpoint_paths=data.get("checkpoint_paths", []),
            final_loss=data.get("final_loss"),
        )
