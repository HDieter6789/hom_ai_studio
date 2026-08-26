from enum import Enum


class DatasetType(str, Enum):
    INSTRUCTION = "instruction"
    CONVERSATION = "conversation"
    TOOL_CALLING = "tool_calling"
    PREFERENCE = "preference"
    AGENT_TRAJECTORY = "agent_trajectory"
    EVALUATION = "evaluation"


class DatasetFormat(str, Enum):
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"


class DatasetStatus(str, Enum):
    UPLOADING = "uploading"
    VALIDATING = "validating"
    READY = "ready"
    INVALID = "invalid"


class ModelProvider(str, Enum):
    QWEN = "qwen"
    MISTRAL = "mistral"
    LLAMA = "llama"
    GEMMA = "gemma"
    OTHER = "other"


class BaseModelStatus(str, Enum):
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class TrainingType(str, Enum):
    LORA = "lora"
    QLORA = "qlora"
    FULL = "full_fine_tuning"
    SFT = "sft"
    DPO = "dpo"


class TrainingPreset(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH_QUALITY = "high_quality"
    CUSTOM = "custom"


class TrainingJobStatus(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def terminal(cls) -> set["TrainingJobStatus"]:
        return {cls.COMPLETED, cls.FAILED, cls.CANCELLED}


# Valid forward transitions for the training job state machine.
TRAINING_JOB_TRANSITIONS: dict[TrainingJobStatus, set[TrainingJobStatus]] = {
    TrainingJobStatus.QUEUED: {TrainingJobStatus.PREPARING, TrainingJobStatus.CANCELLED, TrainingJobStatus.FAILED},
    TrainingJobStatus.PREPARING: {TrainingJobStatus.RUNNING, TrainingJobStatus.CANCELLED, TrainingJobStatus.FAILED},
    TrainingJobStatus.RUNNING: {TrainingJobStatus.EVALUATING, TrainingJobStatus.COMPLETED, TrainingJobStatus.CANCELLED, TrainingJobStatus.FAILED},
    TrainingJobStatus.EVALUATING: {TrainingJobStatus.COMPLETED, TrainingJobStatus.CANCELLED, TrainingJobStatus.FAILED},
    TrainingJobStatus.COMPLETED: set(),
    TrainingJobStatus.FAILED: set(),
    TrainingJobStatus.CANCELLED: set(),
}


class ModelVersionStatus(str, Enum):
    EXPERIMENTAL = "experimental"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
    FAILED = "failed"


class WorkerStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class ComputeProviderKind(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"


class TrainingProviderKind(str, Enum):
    LLAMA_FACTORY = "llama_factory"
    AXOLOTL = "axolotl"


class UserRole(str, Enum):
    ADMIN = "admin"
    ML_ENGINEER = "ml_engineer"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class AuditAction(str, Enum):
    TRAINING_STARTED = "training_started"
    TRAINING_CANCELLED = "training_cancelled"
    MODEL_REGISTERED = "model_registered"
    MODEL_DEPLOYED = "model_deployed"
    MODEL_ARCHIVED = "model_archived"
    DATASET_UPLOADED = "dataset_uploaded"
    DATASET_DELETED = "dataset_deleted"
    CONFIGURATION_CHANGED = "configuration_changed"


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    GPU_UNAVAILABLE = "gpu_unavailable"
    CUDA_OOM = "cuda_out_of_memory"
    DATASET_INVALID = "dataset_invalid"
    PROVIDER_ERROR = "provider_error"
    ARTIFACT_MISSING = "artifact_missing"
    HEALTH_CHECK_FAILED = "health_check_failed"
    CANCELLED_BY_USER = "cancelled_by_user"
    UNKNOWN = "unknown"
