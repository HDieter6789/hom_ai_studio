"""Endpoints called by services/training-worker and services/inference to
report progress back into the single source of truth (Postgres, owned by
apps/api). Protected by a shared internal token, never exposed to the
frontend or to end users."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.deployment import DeploymentStatusCallback
from app.schemas.training import TrainingJobConfigOut, TrainingLogCallback, TrainingStatusCallback
from app.security import verify_internal_token
from app.services import training_service
from app.services.training_service import InvalidJobTransition
from app.services.deployment_service import build_deployment_config, get_deployment
from datetime import datetime, timezone

router = APIRouter(
    prefix="/api/internal", tags=["internal"], dependencies=[Depends(verify_internal_token)]
)


@router.get("/training-jobs/{job_id}/config", response_model=TrainingJobConfigOut)
def get_training_job_config(job_id: str, db: Session = Depends(get_db)):
    return training_service.build_job_config(db, job_id)


@router.get("/deployments/{deployment_id}/config")
def get_deployment_config(deployment_id: str, db: Session = Depends(get_db)):
    return build_deployment_config(db, deployment_id)


@router.post("/training-jobs/{job_id}/status")
def update_training_status(job_id: str, payload: TrainingStatusCallback, db: Session = Depends(get_db)):
    job = training_service.get_job(db, job_id)

    for field in (
        "current_epoch",
        "current_step",
        "total_steps",
        "loss",
        "learning_rate",
        "gpu_memory_used_gb",
        "gpu_utilization_pct",
        "samples_per_sec",
        "tokens_per_sec",
        "progress_pct",
        "provider_run_id",
        "worker_id",
        "output_dir",
        "artifacts",
        "error_code",
        "error_message",
        "failed_step",
        "suggested_actions",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(job, field, value)

    db.add(job)
    db.commit()

    if payload.status is not None:
        try:
            job = training_service.apply_status_transition(db, job, payload.status)
        except InvalidJobTransition as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return {"ok": True}


@router.post("/training-jobs/{job_id}/logs")
def append_training_log(job_id: str, payload: TrainingLogCallback, db: Session = Depends(get_db)):
    training_service.append_log(db, job_id, payload.level, payload.message)
    return {"ok": True}


@router.post("/deployments/{deployment_id}/status")
def update_deployment_status(deployment_id: str, payload: DeploymentStatusCallback, db: Session = Depends(get_db)):
    deployment = get_deployment(db, deployment_id)
    deployment.status = payload.status
    if payload.endpoint_url is not None:
        deployment.endpoint_url = payload.endpoint_url
    if payload.worker_id is not None:
        deployment.worker_id = payload.worker_id
    if payload.detail is not None:
        deployment.last_health_detail = payload.detail
    deployment.last_health_check_at = datetime.now(timezone.utc)
    if deployment.started_at is None and payload.status.value == "healthy":
        deployment.started_at = datetime.now(timezone.utc)
    db.add(deployment)
    db.commit()
    return {"ok": True}
