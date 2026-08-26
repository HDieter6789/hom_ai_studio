from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from hom_core.enums import TrainingJobStatus
from hom_core.schemas.training import (
    TrainingArtifacts,
    TrainingConfig,
    TrainingJobError,
    TrainingLogLine,
    TrainingMetricsSnapshot,
)


@dataclass
class TrainingStatusUpdate:
    status: TrainingJobStatus
    logs: list[TrainingLogLine] = field(default_factory=list)
    metrics: TrainingMetricsSnapshot | None = None
    error: TrainingJobError | None = None


class TrainingProvider(ABC):
    """Interface every training backend (LLaMA-Factory, Axolotl, future
    in-house trainers) must implement. Business logic in apps/api and
    services/training-worker is only ever allowed to talk to this
    interface - never to a concrete trainer's SDK or CLI directly.
    """

    @abstractmethod
    def prepare_training(self, config: TrainingConfig) -> str:
        """Validate the config and materialize whatever the provider needs
        on disk (e.g. a generated YAML config file). Returns a
        provider-specific handle/path that start_training() can use."""

    @abstractmethod
    def start_training(self, config: TrainingConfig, prepared_handle: str) -> str:
        """Launch the training run (as a subprocess or job). Returns a
        provider-specific run id used by get_status()/cancel_training()."""

    @abstractmethod
    def get_status(self, run_id: str) -> TrainingStatusUpdate:
        """Poll the current status, freshest logs and latest metrics for a
        running or finished training run."""

    @abstractmethod
    def cancel_training(self, run_id: str) -> None:
        """Best-effort cooperative cancellation of a running job."""

    @abstractmethod
    def get_artifacts(self, run_id: str) -> TrainingArtifacts:
        """Return the location of produced artifacts (adapter weights,
        merged model, checkpoints) once training has finished."""
