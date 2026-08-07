"""Empirical Challenger Adversarial Stress Testing Suite for Milestone 6.

Stress-tests:
1. SymphonyWorkflowParser with valid, malformed, and edge-case YAML specs.
2. MemoryStoreAdapter sha256 hash chaining under multiple events, multi-event lineage, and remediation rule deduplication.
3. TaskDispatcher with unknown actions, sync/async handlers, and vendor cloning fallbacks.
4. OKFValidator against valid and invalid YAML frontmatter documents and SKILL.md specs.
"""

import asyncio
import datetime
import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from agy_graphify.graph_engine import (
    DAGCycleError,
    StateGraphEngine,
    SymphonyWorkflowParser,
)
from agy_graphify.models.graph_engine_schema import ExecutionMode
from agy_graphify.okf import OKFValidator
from agy_graphify.tasks import TaskDispatcher, vendor_clone_action
from agy_graphify.telemetry import CausalTelemetryEvent, MemoryStoreAdapter

# ============================================================================
# 1. SymphonyWorkflowParser & StateGraphEngine Stress Tests
# ============================================================================


def test_symphony_parser_valid_spec():
    """Test SymphonyWorkflowParser with a well-formed Symphony YAML spec."""
    valid_yaml = """
name: test_symphony_workflow
execution_mode: dag
max_remediations: 5
nodes:
  - id: node_1
    node_type: task
    role: worker
    instructions: Run initial task
  - id: node_2
    node_type: evaluator
    role: reviewer
    dependencies:
      - node_1
    instructions: Review node_1 output
"""
    schema = SymphonyWorkflowParser.parse_yaml_str(valid_yaml)
    assert schema.graph_id == "test_symphony_workflow"
    assert schema.execution_mode == ExecutionMode.dag
    assert schema.max_remediations == 5
    assert len(schema.nodes) == 2
    assert schema.nodes[0].id == "node_1"
    assert schema.nodes[1].dependencies == ["node_1"]


def test_symphony_parser_empty_or_comment_yaml():
    """Test SymphonyWorkflowParser with empty YAML or comment-only string."""
    empty_yaml = "# Just a comment line\n"
    with pytest.raises(ValidationError):
        SymphonyWorkflowParser.parse_yaml_str(empty_yaml)


def test_symphony_parser_malformed_yaml_syntax():
    """Test SymphonyWorkflowParser with malformed YAML syntax."""
    malformed_syntax = """
name: broken_yaml
nodes:
  - id: node1
    dependencies: [unclosed_bracket
"""
    with pytest.raises(yaml.YAMLError):
        SymphonyWorkflowParser.parse_yaml_str(malformed_syntax)


def test_symphony_parser_invalid_enum_node_type():
    """Test SymphonyWorkflowParser with invalid node_type enum value."""
    invalid_enum_yaml = """
name: invalid_enum_workflow
nodes:
  - id: node_1
    node_type: super_custom_nonexistent_type
"""
    with pytest.raises(ValidationError):
        SymphonyWorkflowParser.parse_yaml_str(invalid_enum_yaml)


def test_symphony_parser_max_remediations_unbounded():
    """Adversarial Test: SymphonyWorkflowParser accepts negative or arbitrary max_remediations.

    Empirical Observation: SymphonyWorkflowSpec lacks Field(ge=1, le=10) constraints.
    """
    unbounded_yaml = """
name: unbounded_remediations
max_remediations: -5
nodes:
  - id: node_1
    node_type: task
"""
    schema = SymphonyWorkflowParser.parse_yaml_str(unbounded_yaml)
    # Empirically confirms max_remediations allows negative/unbounded ints
    assert schema.max_remediations == -5


def test_symphony_parser_duplicate_node_ids():
    """Adversarial Test: Duplicate node IDs in spec.

    Empirical check: Verify how StateGraphEngine.validate_dag behaves when duplicate IDs are passed.
    """
    duplicate_id_yaml = """
name: duplicate_node_workflow
nodes:
  - id: duplicate_id
    node_type: task
  - id: duplicate_id
    node_type: evaluator
"""
    schema = SymphonyWorkflowParser.parse_yaml_str(duplicate_id_yaml)
    engine = StateGraphEngine()
    with pytest.raises((DAGCycleError, ValueError)):
        engine.validate_dag(schema.nodes)


def test_symphony_parser_cyclic_dependencies():
    """Test StateGraphEngine static DAG cycle detection."""
    cycle_yaml = """
name: cyclic_workflow
nodes:
  - id: node_a
    node_type: task
    dependencies:
      - node_b
  - id: node_b
    node_type: task
    dependencies:
      - node_a
"""
    schema = SymphonyWorkflowParser.parse_yaml_str(cycle_yaml)
    engine = StateGraphEngine()
    with pytest.raises(DAGCycleError):
        engine.validate_dag(schema.nodes)


def test_symphony_parser_nonexistent_dependency():
    """Test StateGraphEngine validation when depending on missing node."""
    missing_dep_yaml = """
name: missing_dep_workflow
nodes:
  - id: node_a
    node_type: task
    dependencies:
      - non_existent_node
"""
    schema = SymphonyWorkflowParser.parse_yaml_str(missing_dep_yaml)
    engine = StateGraphEngine()
    with pytest.raises(ValueError, match="depends on non-existent node"):
        engine.validate_dag(schema.nodes)


# ============================================================================
# 2. MemoryStoreAdapter Stress Tests
# ============================================================================


def test_memorystore_adapter_sha256_chaining(tmp_path: Path):
    """Test sha256 hash chaining across multiple sequential events in MemoryStoreAdapter."""
    adapter = MemoryStoreAdapter(output_dir=tmp_path)

    events = []
    prev_hash = ""
    for i in range(10):
        ev = CausalTelemetryEvent(
            event_id=f"evt-{i}",
            conversation_id="conv-chain-test",
            step_index=i,
            event_type="STEP_EXECUTE",
            status="DONE",
        )
        adapter.append_causal_event(ev)
        events.append(ev)

        # Verify event causal_hash matches compute_causal_hash with previous hash
        expected_hash = ev.compute_causal_hash(prev_hash)
        assert ev.causal_hash == expected_hash
        prev_hash = ev.causal_hash

    # Verify adapter recorded line in causal_events.jsonl
    jsonl_file = tmp_path / "causal_events.jsonl"
    lines = jsonl_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 10

    # Verify lineage retrieval
    lineage = adapter.get_causal_lineage("conv-chain-test")
    assert len(lineage) == 10
    assert lineage[0].event_id == "evt-0"
    assert lineage[9].event_id == "evt-9"


def test_memorystore_adapter_remediation_deduplication(tmp_path: Path):
    """Test remediation rule deduplication in MemoryStoreAdapter."""
    adapter = MemoryStoreAdapter(output_dir=tmp_path)

    failed_tools_batch1 = [
        {"tool": "pytest", "args": {"path": "tests/test_foo.py"}},
        {"tool": "ruff", "args": {"check": True}},
        {"tool": "pytest", "args": {"path": "tests/test_foo.py"}},  # Duplicate in same batch
    ]
    adapter.record_remediation_rules(failed_tools_batch1)

    rules = adapter.query_remediation_rules()
    assert len(rules) == 2

    # Second batch with duplicate from batch1 and new item
    failed_tools_batch2 = [
        {"tool": "pytest", "args": {"path": "tests/test_foo.py"}},  # Duplicate across batches
        {"tool": "mypy", "args": {"strict": True}},  # New item
    ]
    adapter.record_remediation_rules(failed_tools_batch2)

    rules_updated = adapter.query_remediation_rules()
    assert len(rules_updated) == 3

    # Query filtered by tool_name
    pytest_rules = adapter.query_remediation_rules(tool_name="pytest")
    assert len(pytest_rules) == 1
    assert pytest_rules[0]["tool"] == "pytest"


def test_memorystore_adapter_corrupted_remediation_file_recovery(tmp_path: Path):
    """Adversarial Test: Corrupted / non-list remediation JSON file handling.

    Empirical Observation: record_remediation_rules raises AttributeError when
    remediation_rules.json contains a JSON dict because it lacks isinstance(existing_rules, list) check.
    """
    adapter = MemoryStoreAdapter(output_dir=tmp_path)

    # Write dict instead of list to remediation file
    rem_file = tmp_path / "remediation_rules.json"
    tmp_path.mkdir(parents=True, exist_ok=True)
    rem_file.write_text(json.dumps({"unexpected": "dict_object"}), encoding="utf-8")

    # query_remediation_rules returns empty list gracefully
    assert adapter.query_remediation_rules() == []

    # record_remediation_rules raises AttributeError on dict existing_rules
    with pytest.raises(AttributeError, match="'dict' object has no attribute 'append'"):
        adapter.record_remediation_rules([{"tool": "test", "args": {}}])


def test_memorystore_adapter_unserializable_remediation_args(tmp_path: Path):
    """Adversarial Test: Unserializable args in failed_tools (e.g., datetime object)."""
    adapter = MemoryStoreAdapter(output_dir=tmp_path)

    unserializable_item = {"tool": "custom_tool", "args": {"timestamp": datetime.datetime.now()}}
    with pytest.raises(TypeError):
        adapter.record_remediation_rules([unserializable_item])


# ============================================================================
# 3. TaskDispatcher & vendor_clone_action Stress Tests
# ============================================================================


@pytest.mark.asyncio
async def test_task_dispatcher_registered_and_unknown_actions():
    """Test TaskDispatcher with registered sync/async handlers and unknown action exception."""
    dispatcher = TaskDispatcher()

    def sync_handler(val: int) -> int:
        return val * 2

    async def async_handler(text: str) -> str:
        await asyncio.sleep(0.001)
        return f"echo: {text}"

    dispatcher.register("double", sync_handler)
    dispatcher.register("echo", async_handler)

    res_sync = await dispatcher.dispatch("double", 21)
    assert res_sync == 42

    res_async = await dispatcher.dispatch("echo", "hello world")
    assert res_async == "echo: hello world"

    # Unknown action must raise KeyError
    with pytest.raises(KeyError, match="Unknown action 'nonexistent_action'"):
        await dispatcher.dispatch("nonexistent_action")


@pytest.mark.asyncio
async def test_vendor_clone_fallback(tmp_path: Path):
    """Test vendor_clone_action fallback mechanism when cloning non-existent git repository."""
    vendor_dir = tmp_path / "vendor"

    # Pass a non-existent git repo URL
    cloned_paths = await vendor_clone_action(
        "https://github.com/nonexistent_org/nonexistent_repo_xyz_123.git", vendor_dir=vendor_dir
    )

    assert len(cloned_paths) == 1
    target_path = cloned_paths[0]
    assert target_path.exists()
    assert target_path.name == "nonexistent_repo_xyz_123"

    readme = target_path / "README.md"
    assert readme.exists()
    assert "Vendor dependency placeholder" in readme.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_vendor_clone_existing_directory_skip(tmp_path: Path):
    """Test vendor_clone_action skipping when directory already exists with content."""
    vendor_dir = tmp_path / "vendor"
    existing_repo = vendor_dir / "my_existing_repo"
    existing_repo.mkdir(parents=True)
    (existing_repo / "dummy.txt").write_text("already here", encoding="utf-8")

    cloned_paths = await vendor_clone_action("my_existing_repo", vendor_dir=vendor_dir)
    assert len(cloned_paths) == 1
    assert (cloned_paths[0] / "dummy.txt").read_text(encoding="utf-8") == "already here"


# ============================================================================
# 4. OKFValidator Stress Tests
# ============================================================================


@pytest.mark.asyncio
async def test_okf_validator_valid_doc(tmp_path: Path):
    """Test OKFValidator against a valid OKF markdown document."""
    doc_path = tmp_path / "test_doc.md"
    valid_content = """---
title: Test OKF Spec Document
doc_id: okf-test-001
version: 1.0.0
type: spec
status: draft
author: challenger
tags:
  - test
---

# Test OKF Document

## Overview

This is a test document adhering to OKF specification.
"""
    doc_path.write_text(valid_content, encoding="utf-8")

    validator = OKFValidator(target_dir=tmp_path)
    issues = await validator.validate_file(doc_path)
    assert issues == []


@pytest.mark.asyncio
async def test_okf_validator_valid_skill_md(tmp_path: Path):
    """Test OKFValidator against a valid Antigravity SKILL.md document."""
    skill_path = tmp_path / "SKILL.md"
    valid_skill = """---
name: test-skill
description: A test skill definition for testing purposes.
---

# Test Skill

Instructions for running test skill.
"""
    skill_path.write_text(valid_skill, encoding="utf-8")

    validator = OKFValidator(target_dir=tmp_path)
    issues = await validator.validate_file(skill_path)
    assert issues == []


@pytest.mark.asyncio
async def test_okf_validator_invalid_frontmatter(tmp_path: Path):
    """Test OKFValidator with missing frontmatter header, missing fields, and empty body."""
    # Case 1: Missing frontmatter header
    no_header = tmp_path / "no_header.md"
    no_header.write_text("# Document without frontmatter\n", encoding="utf-8")
    validator = OKFValidator(target_dir=tmp_path)
    issues1 = await validator.validate_file(no_header)
    assert any("Missing YAML frontmatter header" in i for i in issues1)

    # Case 2: Missing required field (e.g., missing doc_id)
    missing_field = tmp_path / "missing_field.md"
    missing_field.write_text(
        """---
title: Missing doc_id
version: 1.0.0
type: guide
status: draft
author: test
tags: [test]
---

## Overview
Content
""",
        encoding="utf-8",
    )
    issues2 = await validator.validate_file(missing_field)
    assert any("doc_id" in i for i in issues2)

    # Case 3: Empty body
    empty_body = tmp_path / "empty_body.md"
    empty_body.write_text(
        """---
title: Title
doc_id: okf-002
version: 1.0.0
type: spec
status: draft
author: test
tags: [test]
---
""",
        encoding="utf-8",
    )
    issues3 = await validator.validate_file(empty_body)
    assert any("OKF document body is empty" in i for i in issues3)

    # Case 4: Missing required section header
    no_required_section = tmp_path / "no_section.md"
    no_required_section.write_text(
        """---
title: Title
doc_id: okf-003
version: 1.0.0
type: spec
status: draft
author: test
tags: [test]
---

# Only Main Header
Some random text without required sections.
""",
        encoding="utf-8",
    )
    issues4 = await validator.validate_file(no_required_section)
    assert any("Missing required section" in i for i in issues4)
