from pydantic import BaseModel


class EvaluationMetrics(BaseModel):
    crm_accuracy: float | None = None
    tool_selection_accuracy: float | None = None
    tool_argument_accuracy: float | None = None
    structured_output_accuracy: float | None = None
    hallucination_rate: float | None = None
    workflow_selection_accuracy: float | None = None
    instruction_following: float | None = None
    response_quality: float | None = None
    latency_ms: float | None = None
    tokens_per_sec: float | None = None


class EvaluationResult(BaseModel):
    model_version_id: str
    dataset_id: str
    metrics: EvaluationMetrics
    sample_count: int
    notes: str | None = None
