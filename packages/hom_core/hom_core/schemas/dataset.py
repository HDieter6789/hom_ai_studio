from pydantic import BaseModel, Field


class DatasetSchemaInfo(BaseModel):
    """Auto-detected shape of a dataset (which keys/roles it uses)."""

    detected_format: str
    fields: list[str] = Field(default_factory=list)
    has_messages: bool = False
    has_tool_calls: bool = False
    has_trajectory_fields: bool = False
    sample_preview: list[dict] = Field(default_factory=list)


class DatasetStats(BaseModel):
    sample_count: int
    valid_count: int
    invalid_count: int
    avg_tokens: float | None = None
    min_tokens: int | None = None
    max_tokens: int | None = None
    possible_duplicates: int = 0


class DatasetValidationResult(BaseModel):
    is_valid: bool
    schema_info: DatasetSchemaInfo
    stats: DatasetStats
    errors: list[str] = Field(default_factory=list)
    invalid_sample_indices: list[int] = Field(default_factory=list)
