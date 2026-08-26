import json

from app.services.dataset_validation import validate_dataset


def _jsonl(records: list[dict]) -> bytes:
    return "\n".join(json.dumps(r) for r in records).encode("utf-8")


def test_valid_conversation_samples_are_recognized():
    raw = _jsonl(
        [
            {
                "messages": [
                    {"role": "system", "content": "You are a CRM AI Agent."},
                    {"role": "user", "content": "Der Kunde hat seit 14 Tagen nicht reagiert."},
                    {"role": "assistant", "content": '{"recommended_action":"follow_up"}'},
                ]
            }
        ]
    )
    result = validate_dataset(raw, "jsonl")

    assert result.is_valid
    assert result.schema_info.detected_format == "conversation"
    assert result.stats.sample_count == 1
    assert result.stats.invalid_count == 0
    assert result.stats.avg_tokens is not None


def test_tool_calling_samples_are_recognized():
    raw = _jsonl(
        [
            {
                "task": "follow_up_customer",
                "context": {"deal_stage": "proposal", "days_since_contact": 14},
                "tool": "crm.create_activity",
                "arguments": {"type": "follow_up"},
                "success": True,
            }
        ]
    )
    result = validate_dataset(raw, "jsonl")

    assert result.is_valid
    assert result.schema_info.detected_format == "tool_calling"


def test_agent_trajectory_samples_are_recognized():
    raw = _jsonl(
        [
            {
                "task": "follow_up_customer",
                "user_request": "Follow up with the customer",
                "context": {},
                "agent_response": "Scheduling a follow up",
                "selected_tools": ["crm.create_activity"],
                "tool_arguments": {"type": "follow_up"},
                "tool_results": {"ok": True},
                "final_result": "done",
                "success": True,
            }
        ]
    )
    result = validate_dataset(raw, "jsonl")

    assert result.is_valid
    assert result.schema_info.detected_format == "agent_trajectory"
    assert result.schema_info.has_trajectory_fields


def test_missing_role_or_content_is_invalid():
    raw = _jsonl([{"messages": [{"role": "user"}]}])
    result = validate_dataset(raw, "jsonl")

    assert not result.is_valid
    assert result.stats.invalid_count == 1
    assert 0 in result.invalid_sample_indices


def test_unrecognized_shape_is_invalid():
    raw = _jsonl([{"foo": "bar"}])
    result = validate_dataset(raw, "jsonl")

    assert not result.is_valid
    assert result.stats.invalid_count == 1


def test_duplicate_samples_are_counted():
    sample = {"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]}
    raw = _jsonl([sample, sample, sample])
    result = validate_dataset(raw, "jsonl")

    assert result.stats.sample_count == 3
    assert result.stats.possible_duplicates == 2


def test_malformed_json_reports_error_without_raising():
    result = validate_dataset(b"{not valid json", "jsonl")

    assert not result.is_valid
    assert result.stats.sample_count == 0
    assert result.errors


def test_csv_format_is_parsed():
    raw = b"task,tool,success\nfollow_up,crm.create_activity,true\n"
    result = validate_dataset(raw, "csv")

    assert result.stats.sample_count == 1
