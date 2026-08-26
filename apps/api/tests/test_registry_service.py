import pytest
from fastapi import HTTPException

from app.models.base_model import BaseModelEntity
from app.models.dataset import Dataset
from app.models.training import TrainingJob
from app.services import registry_service
from hom_core.enums import (
    BaseModelStatus,
    DatasetFormat,
    DatasetStatus,
    DatasetType,
    ModelProvider,
    ModelVersionStatus,
    TrainingJobStatus,
    TrainingPreset,
    TrainingType,
)


def _completed_job(db) -> TrainingJob:
    base_model = BaseModelEntity(name="Qwen2.5-7B", provider=ModelProvider.QWEN, status=BaseModelStatus.AVAILABLE)
    dataset = Dataset(
        name="crm-v1", type=DatasetType.CONVERSATION, format=DatasetFormat.JSONL,
        status=DatasetStatus.READY, storage_key="datasets/x/source.jsonl", sample_count=10,
    )
    db.add_all([base_model, dataset])
    db.flush()
    job = TrainingJob(
        name="test-job", base_model_id=base_model.id, dataset_id=dataset.id,
        training_type=TrainingType.QLORA, preset=TrainingPreset.BALANCED,
        status=TrainingJobStatus.COMPLETED, loss=0.4, output_dir="artifacts/test-job",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_registering_a_job_creates_version_1(db):
    job = _completed_job(db)

    version = registry_service.register_from_job(db, job.id, "HOM-CRM", actor="test@hom.local")

    assert version.model_name == "HOM-CRM"
    assert version.version == 1
    assert version.status == ModelVersionStatus.EXPERIMENTAL
    assert version.display_name == "HOM-CRM-v1"


def test_registering_a_second_job_increments_version(db):
    job_a = _completed_job(db)
    job_b = _completed_job(db)

    registry_service.register_from_job(db, job_a.id, "HOM-CRM", actor="test@hom.local")
    v2 = registry_service.register_from_job(db, job_b.id, "HOM-CRM", actor="test@hom.local")

    assert v2.version == 2


def test_only_completed_jobs_can_be_registered(db):
    job = _completed_job(db)
    job.status = TrainingJobStatus.RUNNING
    db.add(job)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        registry_service.register_from_job(db, job.id, "HOM-CRM", actor="test@hom.local")
    assert exc_info.value.status_code == 400


def test_alias_can_be_repointed(db):
    job_a = _completed_job(db)
    job_b = _completed_job(db)
    v1 = registry_service.register_from_job(db, job_a.id, "HOM-CRM", actor="t@hom.local")
    v2 = registry_service.register_from_job(db, job_b.id, "HOM-CRM", actor="t@hom.local")

    registry_service.set_alias(db, "hom-crm-production", v1.id)
    resolved = registry_service.resolve_alias(db, "hom-crm-production")
    assert resolved.id == v1.id

    registry_service.set_alias(db, "hom-crm-production", v2.id)
    resolved = registry_service.resolve_alias(db, "hom-crm-production")
    assert resolved.id == v2.id
