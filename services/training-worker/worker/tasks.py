import time
from pathlib import Path

from inference.vllm_provider import VLLMInferenceProvider, VLLMNotInstalled

from hom_core.enums import ErrorCode, TrainingJobStatus, TrainingPreset, TrainingType
from hom_core.schemas.deployment import DeploymentRequest
from hom_core.schemas.training import HyperParameters, TrainingConfig
from hom_core.storage.local import LocalStorageProvider

from worker import api_client
from worker.celery_app import celery_app
from worker.config import get_worker_settings
from worker.providers.compute_remote import get_compute_provider
from worker.providers.llama_factory import LlamaFactoryNotInstalled, LlamaFactoryTrainingProvider


def _get_inference_provider() -> VLLMInferenceProvider:
    settings = get_worker_settings()
    return VLLMInferenceProvider(registry_path=str(Path(settings.storage_root) / "inference" / "registry.json"))


def _get_provider() -> LlamaFactoryTrainingProvider:
    settings = get_worker_settings()
    return LlamaFactoryTrainingProvider(
        repo_path=settings.llama_factory_repo,
        work_dir=str(Path(settings.storage_root) / "training_runs"),
        python_executable=settings.python_executable,
    )


def _cancel_flag_path(job_id: str) -> Path:
    settings = get_worker_settings()
    return Path(settings.storage_root) / "training_runs" / job_id / "CANCEL"


@celery_app.task(name="worker.tasks.run_training_job")
def run_training_job(job_id: str) -> None:
    settings = get_worker_settings()
    storage = LocalStorageProvider(settings.storage_root)
    provider = _get_provider()
    compute = get_compute_provider()

    try:
        job_config = api_client.get_training_job_config(job_id)
    except Exception as exc:  # noqa: BLE001 - report any failure via the status callback below
        _fail(job_id, ErrorCode.PROVIDER_ERROR, f"Could not fetch job configuration: {exc}", "fetch_config")
        return

    api_client.post_training_status(job_id, {"status": TrainingJobStatus.PREPARING.value})
    api_client.post_training_log(job_id, "info", f"Preparing training run for '{job_config['training_name']}'")

    if not compute.is_available():
        _fail(
            job_id,
            ErrorCode.GPU_UNAVAILABLE,
            "No GPU is currently available to this worker.",
            "gpu_check",
            suggested_actions=[
                "Register/start a GPU worker (local or remote) before starting training",
                "Check `nvidia-smi` on the worker host",
            ],
        )
        return

    dataset_local_path = storage.resolve_path(job_config["dataset_storage_key"])
    output_dir = str(Path(settings.storage_root) / job_config["output_dir"])
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    config = TrainingConfig(
        job_id=job_id,
        training_name=job_config["training_name"],
        base_model_id=job_config["base_model_id"],
        base_model_local_path=job_config.get("base_model_local_path"),
        base_model_huggingface_id=job_config.get("base_model_huggingface_id"),
        dataset_id=job_config["dataset_id"],
        dataset_path=dataset_local_path,
        dataset_format=job_config["dataset_format"],
        training_type=TrainingType(job_config["training_type"]),
        preset=TrainingPreset(job_config["preset"]),
        hyperparameters=HyperParameters(**job_config["hyperparameters"]),
        output_dir=output_dir,
    )

    try:
        prepared_handle = provider.prepare_training(config)
        run_id = provider.start_training(config, prepared_handle)
    except LlamaFactoryNotInstalled as exc:
        _fail(job_id, ErrorCode.PROVIDER_ERROR, str(exc), "start_training", suggested_actions=[
            "Install LLaMA-Factory in the training-worker image",
            "See the 'LLaMA-Factory' section of the root README.md",
        ])
        return
    except Exception as exc:  # noqa: BLE001
        _fail(job_id, ErrorCode.PROVIDER_ERROR, f"Failed to start training: {exc}", "start_training")
        return

    api_client.post_training_status(
        job_id, {"status": TrainingJobStatus.RUNNING.value, "provider_run_id": run_id, "worker_id": settings.worker_key}
    )
    api_client.post_training_log(job_id, "info", "Training started")

    cancel_flag = _cancel_flag_path(job_id)

    while True:
        time.sleep(settings.status_poll_interval_seconds)

        if cancel_flag.exists():
            provider.cancel_training(run_id)
            api_client.post_training_log(job_id, "info", "Training cancelled by user")
            return  # API already marked the job CANCELLED synchronously when cancel was requested

        update = provider.get_status(run_id)

        for line in update.logs:
            api_client.post_training_log(job_id, line.level, line.message)

        payload: dict = {}
        if update.metrics is not None:
            payload.update(
                current_epoch=update.metrics.epoch,
                current_step=update.metrics.step,
                total_steps=update.metrics.total_steps,
                loss=update.metrics.loss,
                learning_rate=update.metrics.learning_rate,
                progress_pct=(
                    round(100 * update.metrics.step / update.metrics.total_steps, 1)
                    if update.metrics.total_steps
                    else None
                ),
            )
        gpu_snapshots = compute.get_utilization()
        if gpu_snapshots:
            payload["gpu_memory_used_gb"] = gpu_snapshots[0].vram_used_gb
            payload["gpu_utilization_pct"] = gpu_snapshots[0].utilization_pct

        if update.status != TrainingJobStatus.RUNNING:
            payload["status"] = update.status.value

        if update.error is not None:
            payload.update(
                error_code=update.error.error_code.value,
                error_message=update.error.message,
                failed_step=update.error.failed_step,
                suggested_actions=update.error.suggested_actions,
            )

        if payload:
            api_client.post_training_status(job_id, payload)

        if update.status in TrainingJobStatus.terminal():
            if update.status == TrainingJobStatus.COMPLETED:
                artifacts = provider.get_artifacts(run_id)
                api_client.post_training_status(
                    job_id,
                    {
                        "artifacts": artifacts.model_dump(),
                        "output_dir": artifacts.output_dir,
                    },
                )
                api_client.post_training_log(job_id, "info", "Training completed")
            return


@celery_app.task(name="worker.tasks.cancel_training_job")
def cancel_training_job(job_id: str) -> None:
    _cancel_flag_path(job_id).parent.mkdir(parents=True, exist_ok=True)
    _cancel_flag_path(job_id).write_text("1", encoding="utf-8")
    try:
        _get_provider().cancel_training(job_id)
    except Exception:  # noqa: BLE001 - best-effort cancellation
        pass


def _fail(job_id: str, error_code: ErrorCode, message: str, failed_step: str, suggested_actions: list[str] | None = None) -> None:
    try:
        api_client.post_training_log(job_id, "error", message)
        api_client.post_training_status(
            job_id,
            {
                "status": TrainingJobStatus.FAILED.value,
                "error_code": error_code.value,
                "error_message": message,
                "failed_step": failed_step,
                "suggested_actions": suggested_actions or [],
            },
        )
    except Exception:  # noqa: BLE001 - the API being unreachable must not crash the worker
        pass


@celery_app.task(name="worker.tasks.run_deployment")
def run_deployment(deployment_id: str) -> None:
    settings = get_worker_settings()
    provider = _get_inference_provider()

    try:
        deployment_config = api_client.get_deployment_config(deployment_id)
    except Exception as exc:  # noqa: BLE001
        _fail_deployment(deployment_id, f"Could not fetch deployment configuration: {exc}")
        return

    api_client.post_deployment_status(deployment_id, {"status": "starting"})

    request = DeploymentRequest(
        model_version_id=deployment_config["model_version_id"],
        served_model_name=deployment_config["served_model_name"],
        artifact_path=deployment_config["artifact_path"],
        gpu_memory_utilization=deployment_config["gpu_memory_utilization"],
        max_model_len=deployment_config.get("max_model_len"),
    )

    try:
        result = provider.deploy_model(request)
    except VLLMNotInstalled as exc:
        _fail_deployment(deployment_id, str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        _fail_deployment(deployment_id, f"Failed to start vLLM: {exc}")
        return

    # Give the server a moment to boot, then run an initial health check
    # so the UI doesn't show "starting" forever if it came up quickly.
    for _ in range(6):
        time.sleep(5)
        health = provider.health_check(request.served_model_name)
        if health.healthy:
            api_client.post_deployment_status(
                deployment_id,
                {
                    "status": "healthy",
                    "endpoint_url": result.endpoint_url,
                    "worker_id": settings.worker_key,
                    "detail": "Deployment is serving requests",
                },
            )
            return

    api_client.post_deployment_status(
        deployment_id,
        {
            "status": "unhealthy",
            "endpoint_url": result.endpoint_url,
            "worker_id": settings.worker_key,
            "detail": "vLLM process started but did not report healthy within the startup window",
        },
    )


@celery_app.task(name="worker.tasks.stop_deployment")
def stop_deployment(deployment_id: str) -> None:
    try:
        deployment_config = api_client.get_deployment_config(deployment_id)
        _get_inference_provider().stop_model(deployment_config["served_model_name"])
    except Exception:  # noqa: BLE001 - stop is best-effort; API already marks it stopped
        pass


def _fail_deployment(deployment_id: str, detail: str) -> None:
    try:
        api_client.post_deployment_status(deployment_id, {"status": "failed", "detail": detail})
    except Exception:  # noqa: BLE001
        pass


@celery_app.task(name="worker.tasks.send_heartbeat")
def send_heartbeat() -> None:
    settings = get_worker_settings()
    compute = get_compute_provider()
    gpus = [g.model_dump() for g in compute.get_utilization()]
    try:
        api_client.post_worker_heartbeat(
            {
                "worker_key": settings.worker_key,
                "hostname": compute.describe(),
                # The worker process being able to send this heartbeat at
                # all means it's online, whether or not a GPU is attached -
                # GPU absence is conveyed via an empty `gpus` list instead.
                "status": "online",
                "compute_provider": settings.compute_provider,
                "gpus": gpus,
                "running_job_id": None,
            }
        )
    except Exception:  # noqa: BLE001 - heartbeats are best-effort
        pass
