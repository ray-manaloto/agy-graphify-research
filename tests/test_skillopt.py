"""Unit tests for Microsoft SkillOpt Adapter & Trajectory Optimization."""

import json
from pathlib import Path

from agy_graphify.skillopt import SkillOptAdapter, SkillSnapshotContext


def test_skill_snapshot_context(tmp_path: Path) -> None:
    skills_dir = tmp_path / ".agents" / "skills" / "test_skill"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text("Original Skill Content", encoding="utf-8")

    with SkillSnapshotContext(project_dir=tmp_path) as snapshot:
        skill_file.write_text("Mutated Skill Content", encoding="utf-8")
        assert skill_file.read_text(encoding="utf-8") == "Mutated Skill Content"
        snapshot.rollback()
        assert skill_file.read_text(encoding="utf-8") == "Original Skill Content"


def test_skillopt_cold_start_trajectory(tmp_path: Path) -> None:
    adapter = SkillOptAdapter(project_dir=tmp_path)
    stats = adapter.evaluate_trajectories()

    assert stats["total_events"] == 0
    assert stats["failed_tools_count"] == 0
    assert stats["error_rate"] == 0.0


def test_skillopt_lessons_okf_frontmatter(tmp_path: Path) -> None:
    adapter = SkillOptAdapter(project_dir=tmp_path)
    lessons = [{"tool": "run_command", "step_index": 5, "args": {"CommandLine": "invalid_cmd"}}]

    adapter.update_lessons_okf_atomic(lessons)

    lessons_file = tmp_path / "LESSONS.md"
    assert lessons_file.is_file()

    content = lessons_file.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "doc_id: okf-lessons-learned-001" in content
    assert "type: guide" in content
    assert "## Learned Remediation Rules" in content
    assert "run_command" in content


def test_skillopt_malformed_telemetry_resilience(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / ".gemini" / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    telemetry_file = telemetry_dir / "events.jsonl"

    valid_event = {
        "conversation_id": "c1",
        "step_index": 1,
        "event_type": "TOOL",
        "source": "MODEL",
        "status": "DONE",
        "content_summary": "ok",
        "tool_calls": [],
    }

    content = json.dumps(valid_event) + "\nBAD_JSON_LINE\n" + json.dumps(valid_event) + "\n"
    telemetry_file.write_text(content, encoding="utf-8")

    adapter = SkillOptAdapter(project_dir=tmp_path)
    stats = adapter.evaluate_trajectories()
    assert stats["total_events"] == 2


def test_skillopt_lessons_deduplication(tmp_path: Path) -> None:
    adapter = SkillOptAdapter(project_dir=tmp_path)
    lessons = [{"tool": "run_command", "step_index": 5, "args": {"CommandLine": "invalid_cmd"}}]

    adapter.update_lessons_okf_atomic(lessons)
    adapter.update_lessons_okf_atomic(lessons)

    lessons_file = tmp_path / "LESSONS.md"
    content = lessons_file.read_text(encoding="utf-8")
    count = content.count("`run_command`")
    assert count == 1
