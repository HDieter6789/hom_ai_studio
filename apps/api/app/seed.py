"""Populate the database with realistic demo data so the UI looks
meaningful on a fresh install. Kept entirely separate from request-path
production code - run explicitly via `python -m app.seed`.
"""

from datetime import datetime, timedelta, timezone

from app.database import Base, SessionLocal, engine
from app.models.base_model import BaseModelEntity
from app.models.dataset import Dataset
from app.models.deployment import Deployment
from app.models.evaluation import Evaluation
from app.models.registry import ModelAlias, ModelVersion
from app.models.training import TrainingJob, TrainingLog
from app.models.user import User
from app.models.worker import Worker
from app.security import hash_password
from hom_core.enums import (
    BaseModelStatus,
    ComputeProviderKind,
    DatasetFormat,
    DatasetStatus,
    DatasetType,
    DeploymentStatus,
    ModelProvider,
    ModelVersionStatus,
    TrainingJobStatus,
    TrainingPreset,
    TrainingType,
    UserRole,
    WorkerStatus,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Seed data already present, skipping.")
            return

        admin = User(
            email="admin@hom.local",
            hashed_password=hash_password("changeme"),
            full_name="Studio Admin",
            role=UserRole.ADMIN,
        )
        engineer = User(
            email="ml@hom.local",
            hashed_password=hash_password("changeme"),
            full_name="ML Engineer",
            role=UserRole.ML_ENGINEER,
        )
        db.add_all([admin, engineer])

        qwen = BaseModelEntity(
            name="Qwen2.5-7B-Instruct",
            provider=ModelProvider.QWEN,
            huggingface_id="Qwen/Qwen2.5-7B-Instruct",
            architecture="qwen2",
            parameter_count="7B",
            context_length=32768,
            license="apache-2.0",
            status=BaseModelStatus.AVAILABLE,
        )
        mistral = BaseModelEntity(
            name="Mistral-7B-Instruct-v0.3",
            provider=ModelProvider.MISTRAL,
            huggingface_id="mistralai/Mistral-7B-Instruct-v0.3",
            architecture="mistral",
            parameter_count="7B",
            context_length=32768,
            license="apache-2.0",
            status=BaseModelStatus.AVAILABLE,
        )
        llama = BaseModelEntity(
            name="Llama-3.1-8B-Instruct",
            provider=ModelProvider.LLAMA,
            huggingface_id="meta-llama/Llama-3.1-8B-Instruct",
            architecture="llama",
            parameter_count="8B",
            context_length=131072,
            license="llama3.1",
            status=BaseModelStatus.AVAILABLE,
        )
        db.add_all([qwen, mistral, llama])
        db.flush()

        crm_agent_v12 = Dataset(
            name="crm-agent-v12",
            description="CRM tool-calling and agent trajectory samples covering leads, deals and follow-ups.",
            version="v12",
            type=DatasetType.AGENT_TRAJECTORY,
            format=DatasetFormat.JSONL,
            status=DatasetStatus.READY,
            storage_key="datasets/seed/crm-agent-v12.jsonl",
            file_size_bytes=18_400_000,
            sample_count=25_420,
            schema_info={"detected_format": "agent_trajectory", "has_trajectory_fields": True},
            stats={"avg_tokens": 612, "min_tokens": 48, "max_tokens": 4096, "possible_duplicates": 12},
        )
        crm_sft_v1 = Dataset(
            name="CRM Agent Training v1",
            description="Instruction/conversation pairs for CRM recommendation and workflow tasks.",
            version="v1",
            type=DatasetType.CONVERSATION,
            format=DatasetFormat.JSONL,
            status=DatasetStatus.READY,
            storage_key="datasets/seed/crm-sft-v1.jsonl",
            file_size_bytes=9_800_000,
            sample_count=12_050,
            schema_info={"detected_format": "conversation", "has_messages": True},
            stats={"avg_tokens": 340, "min_tokens": 32, "max_tokens": 2048, "possible_duplicates": 4},
        )
        db.add_all([crm_agent_v12, crm_sft_v1])
        db.flush()

        completed_job = TrainingJob(
            name="CRM-Core-v2",
            base_model_id=qwen.id,
            dataset_id=crm_sft_v1.id,
            training_type=TrainingType.QLORA,
            preset=TrainingPreset.BALANCED,
            hyperparameters={"epochs": 3, "learning_rate": 2e-5, "lora_rank": 32},
            status=TrainingJobStatus.COMPLETED,
            provider="llama_factory",
            loss=0.42,
            progress_pct=100,
            output_dir="artifacts/crm-core-v2",
            started_at=now() - timedelta(days=6, hours=3),
            completed_at=now() - timedelta(days=6),
            created_by=engineer.email,
        )
        running_job = TrainingJob(
            name="CRM-Core-v4",
            base_model_id=qwen.id,
            dataset_id=crm_agent_v12.id,
            training_type=TrainingType.QLORA,
            preset=TrainingPreset.HIGH_QUALITY,
            hyperparameters={"epochs": 5, "learning_rate": 1e-5, "lora_rank": 64},
            status=TrainingJobStatus.RUNNING,
            provider="llama_factory",
            current_epoch=3.4,
            current_step=2010,
            total_steps=3000,
            loss=0.58,
            learning_rate=1e-5,
            gpu_memory_used_gb=18.4,
            gpu_utilization_pct=72,
            samples_per_sec=4.2,
            tokens_per_sec=2380,
            progress_pct=67,
            started_at=now() - timedelta(hours=2, minutes=10),
            created_by=engineer.email,
        )
        db.add_all([completed_job, running_job])
        db.flush()

        db.add_all(
            [
                TrainingLog(job_id=running_job.id, level="info", message="Loading dataset crm-agent-v12"),
                TrainingLog(job_id=running_job.id, level="info", message="Loading base model Qwen2.5-7B-Instruct"),
                TrainingLog(job_id=running_job.id, level="info", message="Initializing QLoRA (rank=64, alpha=128)"),
                TrainingLog(job_id=running_job.id, level="info", message="Training started"),
                TrainingLog(job_id=running_job.id, level="info", message="epoch 3.4 | step 2010/3000 | loss 0.58"),
            ]
        )

        v1 = ModelVersion(
            model_name="HOM-CRM",
            version=1,
            base_model_id=mistral.id,
            dataset_id=crm_sft_v1.id,
            training_metrics={"final_loss": 0.61},
            evaluation_metrics={"crm_accuracy": 0.74, "tool_selection_accuracy": 0.79, "latency_ms": 510},
            artifact_location="artifacts/hom-crm-v1",
            status=ModelVersionStatus.ARCHIVED,
        )
        v2 = ModelVersion(
            model_name="HOM-CRM",
            version=2,
            base_model_id=qwen.id,
            dataset_id=crm_sft_v1.id,
            training_job_id=completed_job.id,
            training_metrics={"final_loss": 0.42},
            evaluation_metrics={
                "crm_accuracy": 0.81,
                "tool_selection_accuracy": 0.84,
                "tool_argument_accuracy": 0.80,
                "structured_output_accuracy": 0.88,
                "hallucination_rate": 0.09,
                "workflow_selection_accuracy": 0.77,
                "instruction_following": 0.86,
                "response_quality": 0.82,
                "latency_ms": 460,
                "tokens_per_sec": 61,
            },
            artifact_location="artifacts/hom-crm-v2",
            status=ModelVersionStatus.STAGING,
        )
        v3 = ModelVersion(
            model_name="HOM-CRM",
            version=3,
            base_model_id=qwen.id,
            dataset_id=crm_agent_v12.id,
            evaluation_metrics={
                "crm_accuracy": 0.89,
                "tool_selection_accuracy": 0.93,
                "tool_argument_accuracy": 0.90,
                "structured_output_accuracy": 0.95,
                "hallucination_rate": 0.04,
                "workflow_selection_accuracy": 0.88,
                "instruction_following": 0.92,
                "response_quality": 0.90,
                "latency_ms": 420,
                "tokens_per_sec": 68,
            },
            artifact_location="artifacts/hom-crm-v3",
            status=ModelVersionStatus.PRODUCTION,
            deployment_status="deployed",
        )
        db.add_all([v1, v2, v3])
        db.flush()

        db.add_all(
            [
                Evaluation(model_version_id=v2.id, dataset_id=crm_sft_v1.id, metrics=v2.evaluation_metrics, sample_count=800, notes="Baseline evaluation after SFT."),
                Evaluation(model_version_id=v3.id, dataset_id=crm_agent_v12.id, metrics=v3.evaluation_metrics, sample_count=1200, notes="Post agent-trajectory fine-tune."),
            ]
        )

        db.add(
            Deployment(
                model_version_id=v3.id,
                served_model_name="hom-crm-v3",
                endpoint_url="http://inference:8001/v1",
                status=DeploymentStatus.HEALTHY,
                worker_id="gpu-worker-01",
                started_at=now() - timedelta(days=1),
                last_health_check_at=now() - timedelta(minutes=2),
            )
        )

        db.add_all(
            [
                ModelAlias(alias="hom-crm-production", model_version_id=v3.id),
                ModelAlias(alias="hom-crm-staging", model_version_id=v2.id),
                ModelAlias(alias="hom-crm-latest", model_version_id=v3.id),
            ]
        )

        db.add(
            Worker(
                worker_key="gpu-worker-01",
                hostname="gpu-worker-01",
                status=WorkerStatus.ONLINE,
                compute_provider=ComputeProviderKind.LOCAL,
                gpus=[
                    {
                        "index": 0,
                        "name": "RTX 4090",
                        "vram_total_gb": 24,
                        "vram_used_gb": 18.4,
                        "utilization_pct": 72,
                    }
                ],
                running_job_id=running_job.id,
                last_heartbeat_at=now(),
            )
        )

        db.commit()
        print("Seed data created.")
        print("Login: admin@hom.local / changeme  (role: admin)")
        print("Login: ml@hom.local / changeme      (role: ml_engineer)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
