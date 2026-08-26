from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import worker_client
from app.models.deployment import Deployment
from app.services import audit_service
from app.services.registry_service import get_version
from hom_core.enums import AuditAction, DeploymentStatus


def create_deployment(
    db: Session,
    *,
    model_version_id: str,
    served_model_name: str,
    gpu_memory_utilization: float,
    max_model_len: int | None,
    actor: str,
) -> Deployment:
    version = get_version(db, model_version_id)
    if not version.artifact_location:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Model version has no artifact to deploy")

    existing = db.query(Deployment).filter(Deployment.served_model_name == served_model_name).first()
    if existing and existing.status not in (DeploymentStatus.STOPPED, DeploymentStatus.FAILED):
        raise HTTPException(status.HTTP_409_CONFLICT, f"'{served_model_name}' is already deployed")

    deployment = Deployment(
        model_version_id=model_version_id,
        served_model_name=served_model_name,
        status=DeploymentStatus.PENDING,
        gpu_memory_utilization=gpu_memory_utilization,
        max_model_len=max_model_len,
        created_by=actor,
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    worker_client.enqueue_deployment(deployment.id)

    version.deployment_status = "deploying"
    db.add(version)
    db.commit()

    audit_service.log(
        db,
        action=AuditAction.MODEL_DEPLOYED,
        actor=actor,
        target_type="deployment",
        target_id=deployment.id,
        metadata={"served_model_name": served_model_name, "model_version_id": model_version_id},
    )
    return deployment


def list_deployments(db: Session) -> list[Deployment]:
    return db.query(Deployment).order_by(Deployment.created_at.desc()).all()


def get_deployment(db: Session, deployment_id: str) -> Deployment:
    deployment = db.get(Deployment, deployment_id)
    if deployment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deployment not found")
    return deployment


def build_deployment_config(db: Session, deployment_id: str) -> dict:
    deployment = get_deployment(db, deployment_id)
    version = get_version(db, deployment.model_version_id)
    if not version.artifact_location:
        raise HTTPException(status.HTTP_409_CONFLICT, "Model version has no artifact to deploy")
    return {
        "deployment_id": deployment.id,
        "model_version_id": version.id,
        "served_model_name": deployment.served_model_name,
        "artifact_path": version.artifact_location,
        "gpu_memory_utilization": deployment.gpu_memory_utilization,
        "max_model_len": deployment.max_model_len,
    }


def stop_deployment(db: Session, deployment_id: str, actor: str) -> Deployment:
    deployment = get_deployment(db, deployment_id)
    worker_client.enqueue_stop_deployment(deployment.id)
    deployment.status = DeploymentStatus.STOPPED
    deployment.stopped_at = datetime.now(timezone.utc)
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment
