"""Remote LLaMA-Factory provider for HOM on-demand GPU training.

Architecture:

    AI Studio
        -> training-worker
        -> HOM Training Gateway
        -> Vast.ai GPU
        -> LLaMA-Factory

The remote GPU does not need to exist before the training run. The
Training Gateway provisions and destroys Vast.ai instances on demand.
"""

import base64
import json
from datetime import datetime, timezone

import httpx

from hom_core.enums import (
    ErrorCode,
    TrainingJobStatus,
    TrainingType,
)
from hom_core.providers.training_provider import (
    TrainingProvider,
    TrainingStatusUpdate,
)
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

_TRAINING_TYPE_TO_STAGE = {
    TrainingType.DPO: "dpo",
}


class RemoteAgentUnreachable(
    RuntimeError
):
    pass


class LlamaFactoryRemoteProvider(
    TrainingProvider
):
    def __init__(
        self,
        agent_url: str,
        agent_token: str,
        timeout_seconds: float = 30.0,
    ):
        self.agent_url = (
            agent_url.rstrip("/")
        )

        self.agent_token = (
            agent_token
        )

        self.timeout_seconds = (
            timeout_seconds
        )


    def _headers(
        self,
    ) -> dict[str, str]:
        return {
            "X-Agent-Token":
                self.agent_token
        }


    def _build_config_dict(
        self,
        config: TrainingConfig,
        dataset_name: str,
    ) -> dict:
        hp = config.hyperparameters

        finetuning_type = (
            _TRAINING_TYPE_TO_FINETUNING[
                config.training_type
            ]
        )

        stage = (
            _TRAINING_TYPE_TO_STAGE.get(
                config.training_type,
                "sft",
            )
        )

        model_name = (
            config.base_model_local_path
            or
            config.base_model_huggingface_id
        )

        model_name_lower = str(
            model_name or ""
        ).lower()

        if "qwen" in model_name_lower:
            template = "qwen"
        else:
            template = "default"


        cfg: dict = {
            "stage":
                stage,
            "do_train":
                True,
            "model_name_or_path":
                model_name,
            "dataset":
                dataset_name,
            "template":
                template,
            "finetuning_type":
                finetuning_type,
            "per_device_train_batch_size":
                hp.batch_size,
            "gradient_accumulation_steps":
                hp.gradient_accumulation_steps,
            "learning_rate":
                hp.learning_rate,
            "num_train_epochs":
                hp.epochs,
            "lr_scheduler_type":
                "cosine",
            "warmup_ratio":
                hp.warmup_ratio,
            "weight_decay":
                hp.weight_decay,
            "cutoff_len":
                hp.context_length,
            "bf16":
                hp.bf16,
            "fp16":
                hp.fp16,
            "gradient_checkpointing":
                hp.gradient_checkpointing,

            # Required for live UI metrics.
            "logging_steps":
                1,

            "save_steps":
                5,
            "save_total_limit":
                2,
            "plot_loss":
                True,
            "seed":
                config.seed,
        }


        if finetuning_type == "lora":
            cfg[
                "lora_rank"
            ] = hp.lora_rank

            cfg[
                "lora_alpha"
            ] = hp.lora_alpha

            cfg[
                "lora_dropout"
            ] = hp.lora_dropout

            cfg[
                "lora_target"
            ] = "all"


        if (
            config.training_type
            == TrainingType.QLORA
        ):
            cfg[
                "quantization_bit"
            ] = 4


        cfg.update(
            config.extra
        )


        #
        # Do not allow generic "default" to overwrite the required
        # Qwen template after config.extra is merged.
        #
        if (
            "qwen"
            in model_name_lower
            and str(
                cfg.get(
                    "template",
                    "",
                )
            ).lower()
            in {
                "",
                "default",
                "none",
            }
        ):
            cfg[
                "template"
            ] = "qwen"


        return cfg


    def prepare_training(
        self,
        config: TrainingConfig,
    ) -> str:
        dataset_name = (
            f"job-{config.job_id}"
        )

        cfg_dict = (
            self._build_config_dict(
                config,
                dataset_name,
            )
        )

        return json.dumps(
            {
                "dataset_name":
                    dataset_name,
                "config":
                    cfg_dict,
            }
        )


    def start_training(
        self,
        config: TrainingConfig,
        prepared_handle: str,
    ) -> str:
        handle = json.loads(
            prepared_handle
        )

        try:
            with open(
                config.dataset_path,
                "rb",
            ) as f:
                dataset_b64 = (
                    base64.b64encode(
                        f.read()
                    )
                    .decode("ascii")
                )

        except OSError as exc:
            raise RemoteAgentUnreachable(
                (
                    "Could not read dataset at "
                    f"{config.dataset_path}: "
                    f"{exc}"
                )
            ) from exc


        payload = {
            "job_id":
                config.job_id,
            "dataset_format":
                config.dataset_format,
            "dataset_b64":
                dataset_b64,
            "config":
                handle["config"],
        }


        try:
            response = httpx.post(
                f"{self.agent_url}/jobs",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise RemoteAgentUnreachable(
                (
                    "HOM Training Gateway "
                    "unreachable or rejected "
                    f"job: {exc}"
                )
            ) from exc


        data = response.json()

        run_id = data.get(
            "run_id"
        )

        if not run_id:
            raise RemoteAgentUnreachable(
                (
                    "HOM Training Gateway "
                    "returned no run_id."
                )
            )

        return run_id


    def get_status(
        self,
        run_id: str,
    ) -> TrainingStatusUpdate:
        try:
            response = httpx.get(
                (
                    f"{self.agent_url}/jobs/"
                    f"{run_id}/status"
                ),
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            return TrainingStatusUpdate(
                status=(
                    TrainingJobStatus
                    .FAILED
                ),
                error=TrainingJobError(
                    error_code=(
                        ErrorCode
                        .PROVIDER_ERROR
                    ),
                    message=(
                        "HOM Training Gateway "
                        "unreachable while "
                        "polling status: "
                        f"{exc}"
                    ),
                    failed_step=(
                        "remote_status_poll"
                    ),
                    suggested_actions=[
                        (
                            "Check HOM Training "
                            "Gateway /health"
                        ),
                        (
                            "Check training "
                            "Gateway service logs"
                        ),
                    ],
                ),
            )


        data = response.json()


        logs = [
            TrainingLogLine(
                timestamp=(
                    datetime.now(
                        timezone.utc
                    )
                ),
                level=(
                    line.get(
                        "level",
                        "info",
                    )
                ),
                message=(
                    line.get(
                        "message",
                        ""
                    )
                ),
            )
            for line
            in data.get(
                "logs",
                [],
            )
            if isinstance(
                line,
                dict,
            )
        ]


        metrics = None

        raw_metrics = data.get(
            "metrics"
        )

        if (
            isinstance(
                raw_metrics,
                dict,
            )
            and raw_metrics
        ):
            metrics = (
                TrainingMetricsSnapshot(
                    timestamp=(
                        datetime.now(
                            timezone.utc
                        )
                    ),
                    epoch=(
                        raw_metrics.get(
                            "epoch",
                            0.0,
                        )
                    ),
                    step=(
                        raw_metrics.get(
                            "step",
                            0,
                        )
                    ),
                    total_steps=(
                        raw_metrics.get(
                            "total_steps"
                        )
                    ),
                    loss=(
                        raw_metrics.get(
                            "loss"
                        )
                    ),
                    learning_rate=(
                        raw_metrics.get(
                            "learning_rate"
                        )
                    ),
                    samples_per_sec=(
                        raw_metrics.get(
                            "samples_per_sec"
                        )
                        or
                        raw_metrics.get(
                            "train_samples_per_second"
                        )
                    ),
                    tokens_per_sec=(
                        raw_metrics.get(
                            "tokens_per_sec"
                        )
                    ),
                )
            )


        error = None

        raw_error = data.get(
            "error"
        )

        if (
            isinstance(
                raw_error,
                dict,
            )
            and raw_error
        ):
            raw_code = str(
                raw_error.get(
                    "error_code",
                    ErrorCode
                    .PROVIDER_ERROR
                    .value,
                )
            ).lower()

            try:
                error_code = (
                    ErrorCode(
                        raw_code
                    )
                )

            except ValueError:
                error_code = (
                    ErrorCode
                    .PROVIDER_ERROR
                )


            error = TrainingJobError(
                error_code=error_code,
                message=(
                    raw_error.get(
                        "message",
                        (
                            "Unknown remote "
                            "training error"
                        ),
                    )
                ),
                failed_step=(
                    raw_error.get(
                        "failed_step"
                    )
                ),
                suggested_actions=(
                    raw_error.get(
                        "suggested_actions",
                        [],
                    )
                ),
            )


        raw_status = str(
            data.get(
                "status",
                "failed",
            )
        ).lower()


        try:
            status = (
                TrainingJobStatus(
                    raw_status
                )
            )

        except ValueError:
            status = (
                TrainingJobStatus
                .FAILED
            )

            error = TrainingJobError(
                error_code=(
                    ErrorCode
                    .PROVIDER_ERROR
                ),
                message=(
                    "Unknown status returned "
                    "by HOM Training Gateway: "
                    f"{raw_status}"
                ),
                failed_step=(
                    "remote_status_poll"
                ),
                suggested_actions=[],
            )


        return TrainingStatusUpdate(
            status=status,
            logs=logs,
            metrics=metrics,
            error=error,
        )


    def cancel_training(
        self,
        run_id: str,
    ) -> None:
        try:
            httpx.post(
                (
                    f"{self.agent_url}/jobs/"
                    f"{run_id}/cancel"
                ),
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )

        except httpx.HTTPError:
            pass


    def get_artifacts(
        self,
        run_id: str,
    ) -> TrainingArtifacts:
        response = httpx.get(
            (
                f"{self.agent_url}/jobs/"
                f"{run_id}/artifacts"
            ),
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        data = response.json()

        return TrainingArtifacts(
            output_dir=(
                data.get(
                    "output_dir",
                    "",
                )
            ),
            adapter_path=(
                data.get(
                    "adapter_path"
                )
            ),
            checkpoint_paths=(
                data.get(
                    "checkpoint_paths",
                    [],
                )
            ),
            final_loss=(
                data.get(
                    "final_loss"
                )
            ),
        )
