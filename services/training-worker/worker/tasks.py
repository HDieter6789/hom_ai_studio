import csv
import json
import math
import time
from pathlib import Path

from inference.vllm_provider import VLLMInferenceProvider, VLLMNotInstalled

from hom_core.enums import (
    ErrorCode,
    TrainingJobStatus,
    TrainingPreset,
    TrainingType,
)
from hom_core.schemas.deployment import DeploymentRequest
from hom_core.schemas.training import HyperParameters, TrainingConfig
from hom_core.storage.local import LocalStorageProvider

from worker import api_client
from worker.celery_app import celery_app
from worker.config import get_worker_settings
from worker.providers.compute_remote import get_compute_provider
from worker.providers.llama_factory import (
    LlamaFactoryNotInstalled,
    LlamaFactoryTrainingProvider,
)


def _get_inference_provider() -> VLLMInferenceProvider:
    settings = get_worker_settings()

    return VLLMInferenceProvider(
        registry_path=str(
            Path(settings.storage_root)
            / "inference"
            / "registry.json"
        )
    )


def _get_provider():
    settings = get_worker_settings()

    if (
        settings.compute_provider == "remote"
        and settings.remote_gpu_agent_url
    ):
        from worker.providers.llama_factory_remote import (
            LlamaFactoryRemoteProvider,
        )

        return LlamaFactoryRemoteProvider(
            agent_url=settings.remote_gpu_agent_url,
            agent_token=settings.remote_gpu_agent_token,
        )

    return LlamaFactoryTrainingProvider(
        repo_path=settings.llama_factory_repo,
        work_dir=str(
            Path(settings.storage_root)
            / "training_runs"
        ),
        python_executable=settings.python_executable,
    )


def _cancel_flag_path(job_id: str) -> Path:
    settings = get_worker_settings()

    return (
        Path(settings.storage_root)
        / "training_runs"
        / job_id
        / "CANCEL"
    )


def _count_dataset_rows(
    dataset_path: str,
    dataset_format: str,
) -> int | None:
    """
    Count training examples without loading large datasets fully into RAM.

    Used only for a progress estimate. Failure to count must never prevent
    training from starting.
    """
    path = Path(dataset_path)
    fmt = dataset_format.lower()

    try:

        if fmt == "jsonl":
            with path.open(
                "r",
                encoding="utf-8",
            ) as f:
                return sum(
                    1
                    for line in f
                    if line.strip()
                )

        if fmt == "json":
            data = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )

            if isinstance(data, list):
                return len(data)

            if isinstance(data, dict):
                return 1

        if fmt == "csv":
            with path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as f:
                reader = csv.DictReader(f)

                return sum(
                    1
                    for _ in reader
                )

    except Exception:
        return None

    return None


def _estimate_total_steps(
    config: TrainingConfig,
) -> int | None:
    """
    Estimate optimizer steps for the single-GPU Vast.ai training worker.

    Effective batch size:
        batch_size * gradient_accumulation_steps

    This matches the current single-device training architecture closely
    enough to provide useful UI progress before LLaMA-Factory reports its
    own total step count.
    """
    rows = _count_dataset_rows(
        config.dataset_path,
        config.dataset_format,
    )

    if not rows:
        return None

    hp = config.hyperparameters

    batch_size = max(
        int(hp.batch_size),
        1,
    )

    accumulation = max(
        int(hp.gradient_accumulation_steps),
        1,
    )

    effective_batch = (
        batch_size
        * accumulation
    )

    steps_per_epoch = max(
        math.ceil(
            rows
            / effective_batch
        ),
        1,
    )

    epochs = max(
        float(hp.epochs),
        0.0,
    )

    return max(
        math.ceil(
            steps_per_epoch
            * epochs
        ),
        1,
    )


@celery_app.task(
    name="worker.tasks.run_training_job"
)
def run_training_job(
    job_id: str,
) -> None:
    settings = get_worker_settings()

    storage = LocalStorageProvider(
        settings.storage_root
    )

    provider = _get_provider()
    compute = get_compute_provider()

    try:
        job_config = (
            api_client
            .get_training_job_config(
                job_id
            )
        )

    except Exception as exc:
        _fail(
            job_id,
            ErrorCode.PROVIDER_ERROR,
            (
                "Could not fetch job "
                f"configuration: {exc}"
            ),
            "fetch_config",
        )

        return


    api_client.post_training_status(
        job_id,
        {
            "status":
                TrainingJobStatus
                .PREPARING
                .value
        },
    )

    api_client.post_training_log(
        job_id,
        "info",
        (
            "Preparing training run for "
            f"'{job_config['training_name']}'"
        ),
    )


    if not compute.is_available():
        _fail(
            job_id,
            ErrorCode.GPU_UNAVAILABLE,
            (
                "Remote training "
                "infrastructure is not available."
            ),
            "gpu_check",
            suggested_actions=[
                (
                    "Check HOM Training "
                    "Gateway /health"
                ),
                (
                    "Check remote compute "
                    "provider configuration"
                ),
            ],
        )

        return


    dataset_local_path = (
        storage.resolve_path(
            job_config[
                "dataset_storage_key"
            ]
        )
    )

    output_dir = str(
        Path(settings.storage_root)
        / job_config["output_dir"]
    )

    Path(
        output_dir
    ).mkdir(
        parents=True,
        exist_ok=True,
    )


    config = TrainingConfig(
        job_id=job_id,
        training_name=(
            job_config[
                "training_name"
            ]
        ),
        base_model_id=(
            job_config[
                "base_model_id"
            ]
        ),
        base_model_local_path=(
            job_config.get(
                "base_model_local_path"
            )
        ),
        base_model_huggingface_id=(
            job_config.get(
                "base_model_huggingface_id"
            )
        ),
        dataset_id=(
            job_config[
                "dataset_id"
            ]
        ),
        dataset_path=(
            dataset_local_path
        ),
        dataset_format=(
            job_config[
                "dataset_format"
            ]
        ),
        training_type=TrainingType(
            job_config[
                "training_type"
            ]
        ),
        preset=TrainingPreset(
            job_config[
                "preset"
            ]
        ),
        hyperparameters=HyperParameters(
            **job_config[
                "hyperparameters"
            ]
        ),
        output_dir=output_dir,
    )


    estimated_total_steps = (
        _estimate_total_steps(
            config
        )
    )


    try:
        prepared_handle = (
            provider.prepare_training(
                config
            )
        )

        run_id = (
            provider.start_training(
                config,
                prepared_handle,
            )
        )

    except LlamaFactoryNotInstalled as exc:
        _fail(
            job_id,
            ErrorCode.PROVIDER_ERROR,
            str(exc),
            "start_training",
            suggested_actions=[
                (
                    "Install LLaMA-Factory "
                    "in the training-worker image"
                ),
                (
                    "See the LLaMA-Factory "
                    "section of the root README.md"
                ),
            ],
        )

        return

    except Exception as exc:
        _fail(
            job_id,
            ErrorCode.PROVIDER_ERROR,
            (
                "Failed to start training: "
                f"{exc}"
            ),
            "start_training",
        )

        return


    initial_status = {
        "status":
            TrainingJobStatus
            .RUNNING
            .value,
        "provider_run_id":
            run_id,
        "worker_id":
            settings.worker_key,
    }

    if estimated_total_steps:
        initial_status[
            "total_steps"
        ] = estimated_total_steps

    api_client.post_training_status(
        job_id,
        initial_status,
    )

    api_client.post_training_log(
        job_id,
        "info",
        "Training started",
    )


    cancel_flag = _cancel_flag_path(
        job_id
    )

    while True:
        time.sleep(
            settings
            .status_poll_interval_seconds
        )


        if cancel_flag.exists():
            provider.cancel_training(
                run_id
            )

            api_client.post_training_log(
                job_id,
                "info",
                (
                    "Training cancelled "
                    "by user"
                ),
            )

            return


        update = provider.get_status(
            run_id
        )


        for line in update.logs:
            api_client.post_training_log(
                job_id,
                line.level,
                line.message,
            )


        payload: dict = {}


        if update.metrics is not None:

            epoch = (
                update.metrics.epoch
            )

            step = (
                update.metrics.step
            )

            reported_total_steps = (
                update.metrics.total_steps
            )

            total_steps = (
                reported_total_steps
                or estimated_total_steps
            )


            if (
                (step is None or step == 0)
                and epoch is not None
                and total_steps
                and config.hyperparameters.epochs
            ):
                epoch_fraction = min(
                    max(
                        float(epoch)
                        / float(
                            config
                            .hyperparameters
                            .epochs
                        ),
                        0.0,
                    ),
                    1.0,
                )

                step = min(
                    max(
                        round(
                            epoch_fraction
                            * total_steps
                        ),
                        0,
                    ),
                    total_steps,
                )


            payload[
                "current_epoch"
            ] = epoch

            payload[
                "current_step"
            ] = step

            payload[
                "total_steps"
            ] = total_steps

            payload[
                "loss"
            ] = update.metrics.loss

            payload[
                "learning_rate"
            ] = (
                update
                .metrics
                .learning_rate
            )

            payload[
                "samples_per_sec"
            ] = (
                update
                .metrics
                .samples_per_sec
            )

            payload[
                "tokens_per_sec"
            ] = (
                update
                .metrics
                .tokens_per_sec
            )


            if (
                total_steps
                and step is not None
            ):
                payload[
                    "progress_pct"
                ] = min(
                    round(
                        100
                        * step
                        / total_steps,
                        1,
                    ),
                    100.0,
                )

            elif (
                epoch is not None
                and config
                .hyperparameters
                .epochs
            ):
                payload[
                    "progress_pct"
                ] = min(
                    round(
                        100
                        * float(epoch)
                        / float(
                            config
                            .hyperparameters
                            .epochs
                        ),
                        1,
                    ),
                    100.0,
                )


        gpu_snapshots = (
            compute.get_utilization()
        )

        if gpu_snapshots:
            payload[
                "gpu_memory_used_gb"
            ] = (
                gpu_snapshots[0]
                .vram_used_gb
            )

            payload[
                "gpu_utilization_pct"
            ] = (
                gpu_snapshots[0]
                .utilization_pct
            )


        if update.error is not None:
            payload.update(
                error_code=(
                    update
                    .error
                    .error_code
                    .value
                ),
                error_message=(
                    update
                    .error
                    .message
                ),
                failed_step=(
                    update
                    .error
                    .failed_step
                ),
                suggested_actions=(
                    update
                    .error
                    .suggested_actions
                ),
            )


        #
        # IMPORTANT:
        #
        # After provider.start_training(), AI Studio is already RUNNING.
        # The remote Gateway can still legitimately report PREPARING while
        # Vast.ai is provisioning the machine.
        #
        # Never propagate PREPARING back to AI Studio here, otherwise the
        # backend receives RUNNING -> PREPARING and correctly rejects it
        # with HTTP 409.
        #
        # Only terminal remote states are propagated as state transitions.
        #
        if update.status in (
            TrainingJobStatus.COMPLETED,
            TrainingJobStatus.FAILED,
            TrainingJobStatus.CANCELLED,
        ):
            payload[
                "status"
            ] = update.status.value


        if (
            update.status
            == TrainingJobStatus.COMPLETED
        ):
            payload[
                "progress_pct"
            ] = 100.0

            payload[
                "current_epoch"
            ] = float(
                config
                .hyperparameters
                .epochs
            )

            if estimated_total_steps:
                payload[
                    "current_step"
                ] = (
                    estimated_total_steps
                )

                payload[
                    "total_steps"
                ] = (
                    estimated_total_steps
                )


        if payload:
            api_client.post_training_status(
                job_id,
                payload,
            )


        if update.status in (
            TrainingJobStatus.COMPLETED,
            TrainingJobStatus.FAILED,
            TrainingJobStatus.CANCELLED,
        ):

            if (
                update.status
                == TrainingJobStatus.COMPLETED
            ):
                artifacts = (
                    provider.get_artifacts(
                        run_id
                    )
                )

                artifact_payload = {
                    "artifacts":
                        artifacts.model_dump(),
                    "output_dir":
                        artifacts.output_dir,
                    "progress_pct":
                        100.0,
                }

                if (
                    artifacts.final_loss
                    is not None
                ):
                    artifact_payload[
                        "loss"
                    ] = (
                        artifacts.final_loss
                    )

                api_client.post_training_status(
                    job_id,
                    artifact_payload,
                )

                api_client.post_training_log(
                    job_id,
                    "info",
                    "Training completed",
                )

            return


@celery_app.task(
    name="worker.tasks.cancel_training_job"
)
def cancel_training_job(
    job_id: str,
) -> None:
    _cancel_flag_path(
        job_id
    ).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    _cancel_flag_path(
        job_id
    ).write_text(
        "1",
        encoding="utf-8",
    )

    try:
        _get_provider().cancel_training(
            job_id
        )

    except Exception:
        pass


def _fail(
    job_id: str,
    error_code: ErrorCode,
    message: str,
    failed_step: str,
    suggested_actions: list[str]
    | None = None,
) -> None:
    try:
        api_client.post_training_log(
            job_id,
            "error",
            message,
        )

        api_client.post_training_status(
            job_id,
            {
                "status":
                    TrainingJobStatus
                    .FAILED
                    .value,
                "error_code":
                    error_code.value,
                "error_message":
                    message,
                "failed_step":
                    failed_step,
                "suggested_actions":
                    suggested_actions
                    or [],
            },
        )

    except Exception:
        pass


@celery_app.task(
    name="worker.tasks.run_deployment"
)
def run_deployment(
    deployment_id: str,
) -> None:
    settings = get_worker_settings()

    provider = (
        _get_inference_provider()
    )

    try:
        deployment_config = (
            api_client
            .get_deployment_config(
                deployment_id
            )
        )

    except Exception as exc:
        _fail_deployment(
            deployment_id,
            (
                "Could not fetch deployment "
                f"configuration: {exc}"
            ),
        )

        return


    api_client.post_deployment_status(
        deployment_id,
        {
            "status":
                "starting"
        },
    )


    request = DeploymentRequest(
        model_version_id=(
            deployment_config[
                "model_version_id"
            ]
        ),
        served_model_name=(
            deployment_config[
                "served_model_name"
            ]
        ),
        artifact_path=(
            deployment_config[
                "artifact_path"
            ]
        ),
        gpu_memory_utilization=(
            deployment_config[
                "gpu_memory_utilization"
            ]
        ),
        max_model_len=(
            deployment_config.get(
                "max_model_len"
            )
        ),
    )


    try:
        result = (
            provider.deploy_model(
                request
            )
        )

    except VLLMNotInstalled as exc:
        _fail_deployment(
            deployment_id,
            str(exc),
        )

        return

    except Exception as exc:
        _fail_deployment(
            deployment_id,
            (
                "Failed to start vLLM: "
                f"{exc}"
            ),
        )

        return


    for _ in range(6):
        time.sleep(5)

        health = (
            provider.health_check(
                request.served_model_name
            )
        )

        if health.healthy:
            api_client.post_deployment_status(
                deployment_id,
                {
                    "status":
                        "healthy",
                    "endpoint_url":
                        result.endpoint_url,
                    "worker_id":
                        settings.worker_key,
                    "detail":
                        (
                            "Deployment is "
                            "serving requests"
                        ),
                },
            )

            return


    api_client.post_deployment_status(
        deployment_id,
        {
            "status":
                "unhealthy",
            "endpoint_url":
                result.endpoint_url,
            "worker_id":
                settings.worker_key,
            "detail":
                (
                    "vLLM process started "
                    "but did not report "
                    "healthy within the "
                    "startup window"
                ),
        },
    )


@celery_app.task(
    name="worker.tasks.stop_deployment"
)
def stop_deployment(
    deployment_id: str,
) -> None:
    try:
        deployment_config = (
            api_client
            .get_deployment_config(
                deployment_id
            )
        )

        _get_inference_provider().stop_model(
            deployment_config[
                "served_model_name"
            ]
        )

    except Exception:
        pass


def _fail_deployment(
    deployment_id: str,
    detail: str,
) -> None:
    try:
        api_client.post_deployment_status(
            deployment_id,
            {
                "status":
                    "failed",
                "detail":
                    detail,
            },
        )

    except Exception:
        pass


@celery_app.task(
    name="worker.tasks.send_heartbeat"
)
def send_heartbeat() -> None:
    settings = get_worker_settings()
    compute = get_compute_provider()

    gpus = [
        gpu.model_dump()
        for gpu
        in compute.get_utilization()
    ]

    try:
        api_client.post_worker_heartbeat(
            {
                "worker_key":
                    settings.worker_key,
                "hostname":
                    compute.describe(),
                "status":
                    "online",
                "compute_provider":
                    settings.compute_provider,
                "gpus":
                    gpus,
                "running_job_id":
                    None,
            }
        )

    except Exception:
        pass
