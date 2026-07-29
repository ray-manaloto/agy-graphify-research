"""Async unit tests for TelemetryCollector using pytest."""

import json

import pytest

from agy_graphify.telemetry import TelemetryCollector


@pytest.mark.asyncio
async def test_telemetry_collector(tmp_path):
    # Mock brain log directory structure
    conv_id = "test-conv-123"
    log_dir = tmp_path / "brain" / conv_id / ".system_generated" / "logs"
    log_dir.mkdir(parents=True)

    transcript_file = log_dir / "transcript.jsonl"
    sample_entry = {
        "step_index": 1,
        "type": "USER_INPUT",
        "source": "USER_EXPLICIT",
        "status": "DONE",
        "content": "Run project verification",
        "tool_calls": [],
    }
    transcript_file.write_text(json.dumps(sample_entry) + "\n", encoding="utf-8")

    collector = TelemetryCollector(project_dir=tmp_path, app_data_dir=tmp_path)
    events = await collector.collect_events(conversation_id=conv_id)

    assert len(events) == 1
    assert events[0].conversation_id == conv_id
    assert events[0].event_type == "USER_INPUT"
    assert (tmp_path / ".gemini" / "telemetry" / "events.jsonl").is_file()
    assert (tmp_path / ".gemini" / "telemetry" / "events.msgpack").is_file()
