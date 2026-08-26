from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.registry import ModelAlias, ModelVersion
from app.models.training import TrainingJob
from app.services import audit_service
from hom_core.enums import AuditAction, ModelVersionStatus, TrainingJobStatus


def register_from_job(db: Session, job_id: str, model_name: str, actor: str) -> ModelVersion:
    job = db.get(TrainingJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Training job not found")
    if job.status != TrainingJobStatus.COMPLETED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only completed training jobs can be registered")

    next_version = (
        db.query(func.coalesce(func.max(ModelVersion.version), 0))
        .filter(ModelVersion.model_name == model_name)
        .scalar()
        + 1
    )

    version = ModelVersion(
        model_name=model_name,
        version=next_version,
        base_model_id=job.base_model_id,
        dataset_id=job.dataset_id,
        training_job_id=job.id,
        training_config={
            "training_type": job.training_type.value,
            "preset": job.preset.value,
            "hyperparameters": job.hyperparameters,
        },
        training_metrics={"final_loss": job.loss},
        artifact_location=job.output_dir,
        status=ModelVersionStatus.EXPERIMENTAL,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    audit_service.log(
        db,
        action=AuditAction.MODEL_REGISTERED,
        actor=actor,
        target_type="model_version",
        target_id=version.id,
        metadata={"model_name": model_name, "version": next_version},
    )
    return version


def list_versions(db: Session, model_name: str | None = None) -> list[ModelVersion]:
    query = db.query(ModelVersion)
    if model_name:
        query = query.filter(ModelVersion.model_name == model_name)
    return query.order_by(ModelVersion.model_name, ModelVersion.version.desc()).all()


def get_version(db: Session, version_id: str) -> ModelVersion:
    version = db.get(ModelVersion, version_id)
    if version is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model version not found")
    return version


def set_status(db: Session, version_id: str, new_status: ModelVersionStatus, actor: str) -> ModelVersion:
    version = get_version(db, version_id)
    version.status = new_status
    db.add(version)
    db.commit()
    db.refresh(version)
    if new_status == ModelVersionStatus.ARCHIVED:
        audit_service.log(
            db, action=AuditAction.MODEL_ARCHIVED, actor=actor, target_type="model_version", target_id=version.id
        )
    return version


def set_alias(db: Session, alias: str, model_version_id: str) -> ModelAlias:
    get_version(db, model_version_id)  # 404s if missing
    existing = db.query(ModelAlias).filter(ModelAlias.alias == alias).first()
    if existing:
        existing.model_version_id = model_version_id
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    entry = ModelAlias(alias=alias, model_version_id=model_version_id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_aliases(db: Session) -> list[ModelAlias]:
    return db.query(ModelAlias).order_by(ModelAlias.alias).all()


def resolve_alias(db: Session, alias: str) -> ModelVersion:
    entry = db.query(ModelAlias).filter(ModelAlias.alias == alias).first()
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Alias '{alias}' not found")
    return get_version(db, entry.model_version_id)
