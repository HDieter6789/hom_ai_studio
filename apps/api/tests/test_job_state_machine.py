import pytest

from app.models.base_model import BaseModelEntity
from app.models.dataset import Dataset
from app.models.training import TrainingJob
from app.services.training_service import InvalidJobTransition, apply_status_transition
from hom_core.enums import (
    BaseModelStatus,
    DatasetFormat,
    DatasetStatus,
    DatasetType,
    ModelProvider,
    TrainingJobStatus,
    TrainingPreset,
    TrainingType,
)


def _make_job(db) -> TrainingJob:
    base_model = BaseModelEntity(name="Qwen2.5-7B", provider=ModelProvider.QWEN, status=BaseModelStatus.AVAILABLE)
    dataset = Dataset(
        name="crm-v1",
        type=DatasetType.CONVERSATION,
        format=DatasetFormat.JSONL,
        status=DatasetStatus.READY,
        storage_key="datasets/x/source.jsonl",
        sample_count=10,
    )
    db.add_all([base_model, dataset])
    db.flush()

    job = TrainingJob(
        name="test-job",
        base_model_id=base_model.id,
        dataset_id=dataset.id,
        training_type=TrainingType.QLORA,
        preset=TrainingPreset.BALANCED,
        status=TrainingJobStatus.QUEUED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@pytest.mark.parametrize(
    "path",
    [
        [TrainingJobStatus.PREPARING, TrainingJobStatus.RUNNING, TrainingJobStatus.COMPLETED],
        [TrainingJobStatus.PREPARING, TrainingJobStatus.RUNNING, TrainingJobStatus.EVALUATING, TrainingJobStatus.COMPLETED],
        [TrainingJobStatus.CANCELLED],
        [TrainingJobStatus.PREPARING, TrainingJobStatus.CANCELLED],
        [TrainingJobStatus.PREPARING, TrainingJobStatus.RUNNING, TrainingJobStatus.FAILED],
    ],
)
def test_valid_transition_paths_are_accepted(db, path):
    job = _make_job(db)
    for status in path:
        job = apply_status_transition(db, job, status)
    assert job.status == path[-1]


def test_cannot_skip_from_queued_to_running(db):
    job = _make_job(db)

    with pytest.raises(InvalidJobTransition):
        apply_status_transition(db, job, TrainingJobStatus.RUNNING)


def test_terminal_states_reject_further_transitions(db):
    job = _make_job(db)
    job = apply_status_transition(db, job, TrainingJobStatus.CANCELLED)

    with pytest.raises(InvalidJobTransition):
        apply_status_transition(db, job, TrainingJobStatus.RUNNING)


def test_started_at_is_set_on_first_running_transition(db):
    job = _make_job(db)
    assert job.started_at is None

    job = apply_status_transition(db, job, TrainingJobStatus.PREPARING)
    job = apply_status_transition(db, job, TrainingJobStatus.RUNNING)

    assert job.started_at is not None


def test_completed_at_is_set_on_terminal_transition(db):
    job = _make_job(db)
    job = apply_status_transition(db, job, TrainingJobStatus.PREPARING)
    job = apply_status_transition(db, job, TrainingJobStatus.RUNNING)
    job = apply_status_transition(db, job, TrainingJobStatus.COMPLETED)

    assert job.completed_at is not None
