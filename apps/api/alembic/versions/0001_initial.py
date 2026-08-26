"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "role",
            sa.Enum("admin", "ml_engineer", "developer", "viewer", name="user_role"),
            nullable=False,
            server_default=sa.text("'viewer'"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "base_models",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("qwen", "mistral", "llama", "gemma", "other", name="model_provider"),
            nullable=False,
        ),
        sa.Column("huggingface_id", sa.String(500), nullable=True),
        sa.Column("architecture", sa.String(255), nullable=True),
        sa.Column("parameter_count", sa.String(50), nullable=True),
        sa.Column("context_length", sa.Integer(), nullable=True),
        sa.Column("license", sa.String(255), nullable=True),
        sa.Column("quantization", sa.String(50), nullable=True),
        sa.Column("local_path", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum("available", "downloading", "unavailable", "error", name="base_model_status"),
            nullable=False,
            server_default=sa.text("'unavailable'"),
        ),
    )
    op.create_index("ix_base_models_name", "base_models", ["name"])

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), nullable=False, server_default=sa.text("'v1'")),
        sa.Column(
            "type",
            sa.Enum(
                "instruction",
                "conversation",
                "tool_calling",
                "preference",
                "agent_trajectory",
                "evaluation",
                name="dataset_type",
            ),
            nullable=False,
        ),
        sa.Column("format", sa.Enum("json", "jsonl", "csv", name="dataset_format"), nullable=False),
        sa.Column("source", sa.String(255), nullable=False, server_default=sa.text("'upload'")),
        sa.Column(
            "status",
            sa.Enum("uploading", "validating", "ready", "invalid", name="dataset_status"),
            nullable=False,
            server_default=sa.text("'uploading'"),
        ),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("schema_info", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("stats", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("validation_errors", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("dataset_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_datasets_name", "datasets", ["name"])

    op.create_table(
        "training_jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_model_id", sa.String(), sa.ForeignKey("base_models.id"), nullable=False),
        sa.Column("dataset_id", sa.String(), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("training_type", sa.Enum("lora", "qlora", "full_fine_tuning", "sft", "dpo", name="training_type"), nullable=False),
        sa.Column("preset", sa.Enum("fast", "balanced", "high_quality", "custom", name="training_preset"), nullable=False),
        sa.Column("hyperparameters", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "status",
            sa.Enum(
                "queued", "preparing", "running", "evaluating", "completed", "failed", "cancelled",
                name="training_job_status",
            ),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column("provider", sa.String(50), nullable=False, server_default=sa.text("'llama_factory'")),
        sa.Column("provider_run_id", sa.String(255), nullable=True),
        sa.Column("worker_id", sa.String(255), nullable=True),
        sa.Column("current_epoch", sa.Float(), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("loss", sa.Float(), nullable=True),
        sa.Column("learning_rate", sa.Float(), nullable=True),
        sa.Column("gpu_memory_used_gb", sa.Float(), nullable=True),
        sa.Column("gpu_utilization_pct", sa.Float(), nullable=True),
        sa.Column("samples_per_sec", sa.Float(), nullable=True),
        sa.Column("tokens_per_sec", sa.Float(), nullable=True),
        sa.Column("progress_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "error_code",
            sa.Enum(
                "validation_error", "gpu_unavailable", "cuda_out_of_memory", "dataset_invalid",
                "provider_error", "artifact_missing", "health_check_failed", "cancelled_by_user", "unknown",
                name="error_code",
            ),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("failed_step", sa.String(255), nullable=True),
        sa.Column("suggested_actions", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("output_dir", sa.String(1024), nullable=True),
        sa.Column("artifacts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_training_jobs_name", "training_jobs", ["name"])

    op.create_table(
        "training_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("job_id", sa.String(), sa.ForeignKey("training_jobs.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(20), nullable=False, server_default=sa.text("'info'")),
        sa.Column("message", sa.Text(), nullable=False),
    )
    op.create_index("ix_training_logs_job_id", "training_logs", ["job_id"])

    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("base_model_id", sa.String(), sa.ForeignKey("base_models.id"), nullable=True),
        sa.Column("dataset_id", sa.String(), sa.ForeignKey("datasets.id"), nullable=True),
        sa.Column("training_job_id", sa.String(), sa.ForeignKey("training_jobs.id"), nullable=True),
        sa.Column("training_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("training_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("evaluation_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("artifact_location", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum("experimental", "testing", "staging", "production", "archived", name="model_version_status"),
            nullable=False,
            server_default=sa.text("'experimental'"),
        ),
        sa.Column("deployment_status", sa.String(50), nullable=True),
        sa.UniqueConstraint("model_name", "version", name="uq_model_name_version"),
    )
    op.create_index("ix_model_versions_model_name", "model_versions", ["model_name"])

    op.create_table(
        "model_aliases",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alias", sa.String(255), nullable=False),
        sa.Column("model_version_id", sa.String(), sa.ForeignKey("model_versions.id"), nullable=False),
    )
    op.create_index("ix_model_aliases_alias", "model_aliases", ["alias"], unique=True)

    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version_id", sa.String(), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("dataset_id", sa.String(), sa.ForeignKey("datasets.id"), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_evaluations_model_version_id", "evaluations", ["model_version_id"])

    op.create_table(
        "deployments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version_id", sa.String(), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("served_model_name", sa.String(255), nullable=False),
        sa.Column("endpoint_url", sa.String(500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "starting", "healthy", "unhealthy", "stopped", "failed", name="deployment_status"),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("worker_id", sa.String(255), nullable=True),
        sa.Column("gpu_memory_utilization", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("max_model_len", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_health_detail", sa.String(500), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_deployments_model_version_id", "deployments", ["model_version_id"])
    op.create_index("ix_deployments_served_model_name", "deployments", ["served_model_name"], unique=True)

    op.create_table(
        "workers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("worker_key", sa.String(255), nullable=False),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("online", "offline", "busy", "error", name="worker_status"),
            nullable=False,
            server_default=sa.text("'offline'"),
        ),
        sa.Column(
            "compute_provider",
            sa.Enum("local", "remote", name="compute_provider_kind"),
            nullable=False,
            server_default=sa.text("'local'"),
        ),
        sa.Column("gpus", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("running_job_id", sa.String(255), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workers_worker_key", "workers", ["worker_key"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "action",
            sa.Enum(
                "training_started", "training_cancelled", "model_registered", "model_deployed",
                "model_archived", "dataset_uploaded", "dataset_deleted", "configuration_changed",
                name="audit_action",
            ),
            nullable=False,
        ),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("workers")
    op.drop_table("deployments")
    op.drop_table("evaluations")
    op.drop_table("model_aliases")
    op.drop_table("model_versions")
    op.drop_table("training_logs")
    op.drop_table("training_jobs")
    op.drop_table("datasets")
    op.drop_table("base_models")
    op.drop_table("users")

    for enum_name in (
        "audit_action", "compute_provider_kind", "worker_status", "deployment_status",
        "model_version_status", "error_code", "training_job_status", "training_preset",
        "training_type", "dataset_status", "dataset_format", "dataset_type",
        "base_model_status", "model_provider", "user_role",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
