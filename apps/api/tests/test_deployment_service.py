import pytest
from fastapi import HTTPException

from app.models.registry import ModelVersion
from app.services import deployment_service
from hom_core.enums import ModelVersionStatus


def _version(db, artifact_location: str | None = "artifacts/hom-crm-v3") -> ModelVersion:
    version = ModelVersion(
        model_name="HOM-CRM", version=3, artifact_location=artifact_location, status=ModelVersionStatus.PRODUCTION
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def test_cannot_deploy_a_version_without_an_artifact(db):
    version = _version(db, artifact_location=None)

    with pytest.raises(HTTPException) as exc_info:
        deployment_service.create_deployment(
            db,
            model_version_id=version.id,
            served_model_name="hom-crm-v3",
            gpu_memory_utilization=0.85,
            max_model_len=None,
            actor="t@hom.local",
        )
    assert exc_info.value.status_code == 400


def test_deploying_twice_under_the_same_served_name_conflicts(db):
    version = _version(db)
    deployment_service.create_deployment(
        db, model_version_id=version.id, served_model_name="hom-crm-v3",
        gpu_memory_utilization=0.85, max_model_len=None, actor="t@hom.local",
    )

    with pytest.raises(HTTPException) as exc_info:
        deployment_service.create_deployment(
            db, model_version_id=version.id, served_model_name="hom-crm-v3",
            gpu_memory_utilization=0.85, max_model_len=None, actor="t@hom.local",
        )
    assert exc_info.value.status_code == 409


def test_stopping_frees_up_the_served_name_for_reuse(db):
    version = _version(db)
    deployment = deployment_service.create_deployment(
        db, model_version_id=version.id, served_model_name="hom-crm-v3",
        gpu_memory_utilization=0.85, max_model_len=None, actor="t@hom.local",
    )
    deployment_service.stop_deployment(db, deployment.id, actor="t@hom.local")

    # Should not raise now that the previous deployment is stopped.
    deployment_service.create_deployment(
        db, model_version_id=version.id, served_model_name="hom-crm-v3",
        gpu_memory_utilization=0.85, max_model_len=None, actor="t@hom.local",
    )
