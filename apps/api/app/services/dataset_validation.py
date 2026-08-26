"""Dataset validation, schema detection and statistics.

Supports the three CRM-relevant sample shapes described in the product
spec:
  - chat/instruction samples: {"messages": [{"role": ..., "content": ...}]}
  - tool-calling samples: {"task", "context", "tool", "arguments", "success"}
  - agent trajectory samples: {"task", "user_request", "context",
    "agent_response", "selected_tools", "tool_arguments", "tool_results",
    "final_result", "success", "human_feedback", "reward", "timestamp"}
"""

import csv
import hashlib
import io
import json
from typing import Any, BinaryIO

from hom_core.schemas.dataset import DatasetSchemaInfo, DatasetStats, DatasetValidationResult

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - tiktoken should always be installed
    _ENCODING = None


def _count_tokens(text: str) -> int:
    if _ENCODING is not None:
        return len(_ENCODING.encode(text))
    # Fallback heuristic, still deterministic and good enough for stats.
    return max(1, len(text) // 4)


TRAJECTORY_FIELDS = {
    "task",
    "user_request",
    "context",
    "agent_response",
    "selected_tools",
    "tool_arguments",
    "tool_results",
    "final_result",
    "success",
}

TOOL_CALL_FIELDS = {"task", "context", "tool", "arguments", "success"}


def _sample_text(sample: dict) -> str:
    if "messages" in sample and isinstance(sample["messages"], list):
        return "\n".join(str(m.get("content", "")) for m in sample["messages"] if isinstance(m, dict))
    return json.dumps(sample, ensure_ascii=False)


def _is_valid_sample(sample: Any) -> tuple[bool, str | None]:
    if not isinstance(sample, dict):
        return False, "sample is not a JSON object"
    if "messages" in sample:
        messages = sample["messages"]
        if not isinstance(messages, list) or len(messages) == 0:
            return False, "'messages' must be a non-empty list"
        for m in messages:
            if not isinstance(m, dict) or "role" not in m or "content" not in m:
                return False, "each message needs 'role' and 'content'"
        return True, None
    if TOOL_CALL_FIELDS.issubset(sample.keys()):
        return True, None
    if TRAJECTORY_FIELDS.issubset(sample.keys()):
        return True, None
    return False, "sample does not match any known dataset schema"


def parse_samples(raw: bytes, fmt: str) -> list[Any]:
    if fmt == "jsonl":
        samples = []
        for line in raw.decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))
        return samples
    if fmt == "json":
        parsed = json.loads(raw.decode("utf-8"))
        return parsed if isinstance(parsed, list) else [parsed]
    if fmt == "csv":
        text = raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]
    raise ValueError(f"Unsupported dataset format: {fmt}")


def detect_schema(samples: list[Any]) -> DatasetSchemaInfo:
    fields: set[str] = set()
    has_messages = False
    has_tool_calls = False
    has_trajectory = False
    for sample in samples[:200]:
        if not isinstance(sample, dict):
            continue
        fields.update(sample.keys())
        if "messages" in sample:
            has_messages = True
        if TOOL_CALL_FIELDS.issubset(sample.keys()) or "tool" in sample:
            has_tool_calls = True
        if TRAJECTORY_FIELDS.issubset(sample.keys()):
            has_trajectory = True

    if has_trajectory:
        detected = "agent_trajectory"
    elif has_tool_calls:
        detected = "tool_calling"
    elif has_messages:
        detected = "conversation"
    else:
        detected = "unknown"

    return DatasetSchemaInfo(
        detected_format=detected,
        fields=sorted(fields),
        has_messages=has_messages,
        has_tool_calls=has_tool_calls,
        has_trajectory_fields=has_trajectory,
        sample_preview=[s for s in samples[:5] if isinstance(s, dict)],
    )


def validate_dataset(raw: bytes, fmt: str) -> DatasetValidationResult:
    errors: list[str] = []
    try:
        samples = parse_samples(raw, fmt)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        return DatasetValidationResult(
            is_valid=False,
            schema_info=DatasetSchemaInfo(detected_format="unknown"),
            stats=DatasetStats(sample_count=0, valid_count=0, invalid_count=0),
            errors=[f"Could not parse file as {fmt}: {exc}"],
        )

    schema_info = detect_schema(samples)

    token_counts: list[int] = []
    invalid_indices: list[int] = []
    seen_hashes: dict[str, int] = {}
    duplicates = 0

    for idx, sample in enumerate(samples):
        is_valid, reason = _is_valid_sample(sample)
        if not is_valid:
            invalid_indices.append(idx)
            if reason and len(errors) < 50:
                errors.append(f"sample {idx}: {reason}")
            continue

        text = _sample_text(sample)
        token_counts.append(_count_tokens(text))

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in seen_hashes:
            duplicates += 1
        else:
            seen_hashes[digest] = idx

    stats = DatasetStats(
        sample_count=len(samples),
        valid_count=len(samples) - len(invalid_indices),
        invalid_count=len(invalid_indices),
        avg_tokens=(sum(token_counts) / len(token_counts)) if token_counts else None,
        min_tokens=min(token_counts) if token_counts else None,
        max_tokens=max(token_counts) if token_counts else None,
        possible_duplicates=duplicates,
    )

    return DatasetValidationResult(
        is_valid=len(samples) > 0 and stats.invalid_count == 0,
        schema_info=schema_info,
        stats=stats,
        errors=errors,
        invalid_sample_indices=invalid_indices[:200],
    )
