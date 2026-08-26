from abc import ABC, abstractmethod

from hom_core.schemas.deployment import DeploymentRequest, DeploymentResult, HealthCheckResult


class InferenceProvider(ABC):
    """Interface every inference backend (vLLM today, others later) must
    implement so that deployment logic never depends on vLLM directly."""

    @abstractmethod
    def deploy_model(self, request: DeploymentRequest) -> DeploymentResult:
        """Start serving a model artifact and return how to reach it."""

    @abstractmethod
    def stop_model(self, served_model_name: str) -> None:
        """Stop serving a model previously deployed by this provider."""

    @abstractmethod
    def health_check(self, served_model_name: str) -> HealthCheckResult:
        """Check whether a deployed model is currently healthy/reachable."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """List the served_model_names currently deployed by this provider."""
