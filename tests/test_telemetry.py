"""Async unit tests for TelemetryCollector using pytest."""

import json

import pytest

from agy_graphify.telemetry import (
    CausalTelemetryEvent,
    MemoryStoreAdapter,
    TelemetryCollector,
)


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
    assert (tmp_path / ".gemini" / "telemetry" / "causal_events.jsonl").is_file()


@pytest.mark.asyncio
async def test_telemetry_collector_malformed_lines(tmp_path):
    conv_id = "test-conv-456"
    log_dir = tmp_path / "brain" / conv_id / ".system_generated" / "logs"
    log_dir.mkdir(parents=True)

    transcript_file = log_dir / "transcript.jsonl"
    lines = [
        json.dumps("primitive string line"),
        json.dumps(12345),
        json.dumps(
            {
                "step_index": 1,
                "type": "TOOL",
                "status": "failed",
                "tool_calls": [{"name": "cmd1", "args": {}}],
            }
        ),
        json.dumps(
            {
                "step_index": 2,
                "type": "TOOL",
                "status": "ERROR",
                "tool_calls": [{"name": "cmd2", "args": {}}],
            }
        ),
        json.dumps({"step_index": 3, "type": "TOOL", "status": "DONE", "tool_calls": None}),
    ]
    transcript_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    collector = TelemetryCollector(project_dir=tmp_path, app_data_dir=tmp_path)
    events = await collector.collect_events(conversation_id=conv_id)

    assert len(events) == 3
    failed = collector.analyze_failed_tools(events)
    assert len(failed) == 2
    assert (tmp_path / ".gemini" / "telemetry" / "remediation_rules.json").is_file()


@pytest.mark.asyncio
async def test_telemetry_nonexistent_conversation(tmp_path):
    collector = TelemetryCollector(project_dir=tmp_path, app_data_dir=tmp_path)
    events = await collector.collect_events(conversation_id="nonexistent-conv-999")
    assert events == []


def test_causal_telemetry_event_hash_chaining():
    event1 = CausalTelemetryEvent(
        event_id="ev-1",
        conversation_id="conv-100",
        step_index=1,
        event_type="TOOL_CALL",
        status="DONE",
    )
    hash1 = event1.compute_causal_hash("")
    assert len(hash1) == 64

    event2 = CausalTelemetryEvent(
        event_id="ev-2",
        conversation_id="conv-100",
        step_index=2,
        event_type="TOOL_CALL",
        status="DONE",
    )
    hash2 = event2.compute_causal_hash(hash1)
    assert len(hash2) == 64
    assert hash1 != hash2


def test_memory_store_adapter_causal_events(tmp_path):
    adapter = MemoryStoreAdapter(output_dir=tmp_path)
    event1 = CausalTelemetryEvent(
        event_id="ev-1",
        conversation_id="conv-101",
        step_index=1,
        event_type="SUBAGENT_SPAWN",
    )
    adapter.append_causal_event(event1)

    lineage = adapter.get_causal_lineage("conv-101")
    assert len(lineage) == 1
    assert lineage[0].event_id == "ev-1"
    assert lineage[0].causal_hash != ""

    causal_file = tmp_path / "causal_events.jsonl"
    assert causal_file.is_file()
    lines = causal_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_memory_store_adapter_remediation_rules(tmp_path):
    adapter = MemoryStoreAdapter(output_dir=tmp_path)
    assert adapter.query_remediation_rules() == []

    failed_tools = [
        {
            "conversation_id": "c1",
            "step_index": 1,
            "tool": "git_push",
            "args": {"remote": "origin"},
        },
        {
            "conversation_id": "c1",
            "step_index": 2,
            "tool": "pytest",
            "args": {"target": "tests/test_okf.py"},
        },
    ]
    adapter.record_remediation_rules(failed_tools)

    rules = adapter.query_remediation_rules()
    assert len(rules) == 2

    git_rules = adapter.query_remediation_rules("git_push")
    assert len(git_rules) == 1
    assert git_rules[0]["tool"] == "git_push"

    nonexistent_rules = adapter.query_remediation_rules("nonexistent_tool")
    assert len(nonexistent_rules) == 0

    # Test deduplication
    adapter.record_remediation_rules(failed_tools)
    assert len(adapter.query_remediation_rules()) == 2


def test_memory_store_adapter_tail_hash_seeding(tmp_path):
    adapter1 = MemoryStoreAdapter(output_dir=tmp_path)
    event1 = CausalTelemetryEvent(
        event_id="ev-seed-1",
        conversation_id="conv-seed-100",
        step_index=1,
        event_type="TOOL_CALL",
    )
    adapter1.append_causal_event(event1)
    hash1 = event1.causal_hash
    assert hash1 != ""

    # Create new adapter instance pointing to same directory with existing causal_events.jsonl
    adapter2 = MemoryStoreAdapter(output_dir=tmp_path)
    assert adapter2._last_hash == hash1

    event2 = CausalTelemetryEvent(
        event_id="ev-seed-2",
        conversation_id="conv-seed-100",
        step_index=2,
        event_type="TOOL_CALL",
    )
    adapter2.append_causal_event(event2)
    expected_hash2 = event2.compute_causal_hash(hash1)
    assert event2.causal_hash == expected_hash2
