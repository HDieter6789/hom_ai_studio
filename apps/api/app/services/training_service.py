from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import worker_client
from app.models.base_model import BaseModelEntity
from app.models.dataset import Dataset
from app.models.training import TrainingJob, TrainingLog
from app.schemas.training import TrainingJobConfigOut
from app.services import audit_service
from app.services.training_config import (
    build_hyperparameters,
    resolve_training_type,
    validate_training_inputs,
)
from hom_core.enums import (
    TRAINING_JOB_TRANSITIONS,
    AuditAction,
    TrainingJobStatus,
    TrainingPreset,
    TrainingType,
)


class InvalidJobTransition(Exception):
    pass


def create_training_job(
    db: Session,
    *,
    name: str,
    base_model_id: str,
    dataset_id: str,
    preset: TrainingPreset,
    training_type: TrainingType | None,
    hyperparameter_overrides: dict | None,
    actor: str,
) -> TrainingJob:
    validate_training_inputs(db, base_model_id, dataset_id)
    resolved_type = resolve_training_type(preset, training_type)
    hyperparameters = build_hyperparameters(preset, hyperparameter_overrides)

    job = TrainingJob(
        name=name,
        base_model_id=base_model_id,
        dataset_id=dataset_id,
        training_type=resolved_type,
        preset=preset,
        hyperparameters=hyperparameters.model_dump(),
        status=TrainingJobStatus.QUEUED,
        created_by=actor,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    worker_client.enqueue_training_job(job.id)

    audit_service.log(
        db,
        action=AuditAction.TRAINING_STARTED,
        actor=actor,
        target_type="training_job",
        target_id=job.id,
        metadata={"name": name, "preset": preset.value, "training_type": resolved_type.value},
    )
    return job


def list_jobs(db: Session) -> list[TrainingJob]:
    return db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).all()


def get_job(db: Session, job_id: str) -> TrainingJob:
    job = db.get(TrainingJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Training job not found")
    return job


def cancel_job(db: Session, job_id: str, actor: str) -> TrainingJob:
    job = get_job(db, job_id)
    if job.status in TrainingJobStatus.terminal():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Job already in terminal state '{job.status.value}'")

    worker_client.enqueue_cancel_training_job(job.id)
    apply_status_transition(db, job, TrainingJobStatus.CANCELLED)

    audit_service.log(
        db,
        action=AuditAction.TRAINING_CANCELLED,
        actor=actor,
        target_type="training_job",
        target_id=job.id,
    )
    return job


def apply_status_transition(db: Session, job: TrainingJob, new_status: TrainingJobStatus) -> TrainingJob:
    allowed = TRAINING_JOB_TRANSITIONS.get(job.status, set())
    if new_status != job.status and new_status not in allowed:
        raise InvalidJobTransition(
            f"Cannot transition training job from '{job.status.value}' to '{new_status.value}'"
        )

    if new_status == TrainingJobStatus.RUNNING and job.started_at is None:
        job.started_at = datetime.now(timezone.utc)
    if new_status in TrainingJobStatus.terminal():
        job.completed_at = datetime.now(timezone.utc)

    job.status = new_status
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def append_log(db: Session, job_id: str, level: str, message: str, timestamp: datetime | None = None) -> None:
    log = TrainingLog(job_id=job_id, level=level, message=message)
    if timestamp is not None:
        log.timestamp = timestamp
    db.add(log)
    db.commit()


def build_job_config(db: Session, job_id: str) -> TrainingJobConfigOut:
    job = get_job(db, job_id)
    base_model = db.get(BaseModelEntity, job.base_model_id)
    dataset = db.get(Dataset, job.dataset_id)
    if base_model is None or dataset is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Training job references a deleted base model or dataset")

    return TrainingJobConfigOut(
        job_id=job.id,
        training_name=job.name,
        base_model_id=base_model.id,
        base_model_local_path=base_model.local_path,
        base_model_huggingface_id=base_model.huggingface_id,
        dataset_id=dataset.id,
        dataset_storage_key=dataset.storage_key,
        dataset_format=dataset.format.value,
        training_type=job.training_type,
        preset=job.preset,
        hyperparameters=job.hyperparameters,
        output_dir=f"artifacts/{job.id}",
    )


def recent_logs(db: Session, job_id: str, limit: int = 500) -> list[TrainingLog]:
    return (
        db.query(TrainingLog)
        .filter(TrainingLog.job_id == job_id)
        .order_by(TrainingLog.timestamp.desc())
        .limit(limit)
        .all()[::-1]
    )
