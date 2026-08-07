"""Microsoft SkillOpt Adaptation for Self-Learning Prompt Optimization & Trajectory Evaluation."""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .logger import logger
from .telemetry import TelemetryCollector, TelemetryEvent


class SkillSnapshotContext:
    """Context manager creating snapshot backups of active skill directories with automatic rollback capability."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or Path.cwd()).resolve()
        self.temp_dir: Path | None = None
        self.skills_dirs = [
            (self.project_dir / ".agents" / "skills").resolve(),
            (self.project_dir / ".gemini" / "skills").resolve(),
        ]
        self.created_dirs: list[Path] = []

    def __enter__(self) -> "SkillSnapshotContext":
        self.temp_dir = Path(tempfile.mkdtemp(prefix="skillopt_snapshot_"))
        for s_dir in self.skills_dirs:
            if s_dir.is_dir():
                try:
                    rel_path = s_dir.relative_to(self.project_dir)
                except ValueError:
                    rel_path = Path(s_dir.name)
                target_dest = self.temp_dir / rel_path
                shutil.copytree(s_dir, target_dest, dirs_exist_ok=True)
            else:
                self.created_dirs.append(s_dir)
        logger.info(f"Created skill prompts snapshot in {self.temp_dir}")
        return self

    def rollback(self) -> None:
        """Rollback skill directories to snapshot state."""
        if not self.temp_dir or not self.temp_dir.is_dir():
            logger.warning("No snapshot directory available for rollback.")
            return

        for s_dir in self.skills_dirs:
            try:
                rel_path = s_dir.relative_to(self.project_dir)
            except ValueError:
                rel_path = Path(s_dir.name)
            snapshot_src = self.temp_dir / rel_path
            if snapshot_src.is_dir():
                shutil.rmtree(s_dir, ignore_errors=True)
                shutil.copytree(snapshot_src, s_dir, dirs_exist_ok=True)
                logger.warning(f"Rolled back skill directory {s_dir} to snapshot state.")
            elif s_dir in self.created_dirs and s_dir.is_dir():
                shutil.rmtree(s_dir, ignore_errors=True)
                logger.warning(f"Removed newly created skill directory {s_dir} on rollback.")

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        if self.temp_dir and self.temp_dir.is_dir():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


class SkillOptAdapter:
    """Adapts Microsoft SkillOpt trajectory scoring and prompt optimization for Antigravity skills & LESSONS.md."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or Path.cwd()).resolve()
        self.telemetry_file = self.project_dir / ".gemini" / "telemetry" / "events.jsonl"
        self.lessons_file = self.project_dir / "LESSONS.md"

    def evaluate_trajectories(self) -> dict[str, Any]:
        """Evaluate conversation event trajectories from telemetry. Cold-start safe."""
        if not self.telemetry_file.is_file():
            logger.info(
                "Cold-start: Telemetry events log not found. Returning baseline trajectory score 0.0."
            )
            return {
                "total_events": 0,
                "failed_tools_count": 0,
                "error_rate": 0.0,
                "remediations": [],
            }

        collector = TelemetryCollector(project_dir=self.project_dir)
        events: list[TelemetryEvent] = []

        try:
            content = self.telemetry_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                    if isinstance(raw, dict):
                        events.append(TelemetryEvent(**raw))
                except Exception as exc:
                    logger.warning(
                        f"Skipping malformed line in telemetry log {self.telemetry_file}: {exc}"
                    )
        except Exception as exc:
            logger.warning(f"Error reading telemetry log {self.telemetry_file}: {exc}")

        failed_tools = collector.analyze_failed_tools(events)
        total_count = len(events)
        failed_count = len(failed_tools)
        raw_error_rate = (failed_count / total_count) if total_count > 0 else 0.0
        error_rate = min(1.0, max(0.0, raw_error_rate))

        return {
            "total_events": total_count,
            "failed_tools_count": failed_count,
            "error_rate": round(error_rate, 4),
            "remediations": failed_tools,
        }

    def update_lessons_okf_atomic(self, new_lessons: list[dict[str, Any]]) -> None:
        """Atomically append learned patterns to LESSONS.md with OKF frontmatter."""
        now_iso = datetime.now(UTC).isoformat()
        created_at_str = now_iso

        existing_entries: list[str] = []
        seen_entries: set[str] = set()
        if self.lessons_file.is_file():
            content = self.lessons_file.read_text(encoding="utf-8")
            # Preserve created_at timestamp if present
            for line in content.splitlines():
                if line.startswith("created_at:"):
                    created_at_str = line.split("created_at:", 1)[1].strip().strip("\"'")
                    break
            if "## Learned Remediation Rules" in content:
                _, existing_body = content.split("## Learned Remediation Rules", 1)
                for line in existing_body.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("- **Tool**") and stripped not in seen_entries:
                        existing_entries.append(stripped)
                        seen_entries.add(stripped)

        frontmatter = f"""---
title: Self-Learning Telemetry Lessons & Remediation Rules
doc_id: okf-lessons-learned-001
version: 1.0.0
type: guide
status: approved
author: skillopt-learning-agent
created_at: "{created_at_str}"
updated_at: "{now_iso}"
tags:
  - self-learning
  - telemetry
  - remediation
  - okf
  - skillopt
---

# Self-Learning Telemetry Lessons & Remediation Rules

## Overview

This Open Knowledge Format (OKF) document records automated anti-patterns, tool failure remediations, and prompt optimization rules extracted by `SkillOptAdapter`.

## Learned Remediation Rules

"""
        body_entries = list(existing_entries)

        for item in new_lessons:
            rule_entry = f"- **Tool**: `{item.get('tool', 'unknown')}` | **Step**: `{item.get('step_index', 0)}` | **Args**: `{item.get('args', {})}`"
            if rule_entry not in seen_entries:
                body_entries.append(rule_entry)
                seen_entries.add(rule_entry)

        full_content = frontmatter + "\n".join(body_entries) + ("\n" if body_entries else "")

        with tempfile.NamedTemporaryFile(
            "w", dir=self.project_dir, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(full_content)
            tmp_name = tmp.name

        os.replace(tmp_name, self.lessons_file)
        logger.info(f"Updated OKF-compliant {self.lessons_file}")

    def optimize_prompts(self, dry_run: bool = False) -> dict[str, Any]:
        """Optimize skill prompts with snapshot backup and mutation rollback."""
        stats = self.evaluate_trajectories()

        if stats["failed_tools_count"] == 0:
            logger.info("No failed tools detected in trajectories. Prompt optimization skipped.")
            return {"status": "skipped", "reason": "Zero failures detected", "stats": stats}

        if dry_run:
            logger.info(
                f"[Dry Run] Evaluated {stats['failed_tools_count']} failed tool executions for prompt optimization."
            )
            return {"status": "dry_run_passed", "stats": stats}

        with SkillSnapshotContext(project_dir=self.project_dir) as snapshot:
            self.update_lessons_okf_atomic(stats["remediations"])

            # Verify high error rate safety threshold (>50% error rate triggers rollback)
            if stats["error_rate"] > 0.5:
                logger.warning(
                    f"Error rate ({stats['error_rate']}) exceeds 50% safety limit. Triggering rollback."
                )
                snapshot.rollback()
                return {"status": "rolled_back", "reason": "Error rate > 50%", "stats": stats}

            return {"status": "optimized", "stats": stats}

    def mutate_subagent_prompts(self, role: str, lessons: list[dict[str, Any]]) -> None:
        """Mutate subagent skill prompts in .gemini/skills/ with learned remediation rules."""
        skill_file = self.project_dir / ".gemini" / "skills" / role / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        if not skill_file.is_file():
            skill_file.write_text(f"# Skill: {role}\n", encoding="utf-8")

        content = skill_file.read_text(encoding="utf-8")
        append_text = "\n\n## Learned Remediation Rules\n"
        for lesson in lessons:
            append_text += (
                f"- **Avoid**: {lesson.get('tool', 'unknown')} with args {lesson.get('args', {})}\n"
            )

        with SkillSnapshotContext(project_dir=self.project_dir) as snapshot:
            skill_file.write_text(content + append_text, encoding="utf-8")

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest"], capture_output=True, text=True, check=True
                )
                logger.info(f"Prompt mutated for {role} successfully.")
            except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
                logger.error(f"Tests failed after mutating prompt for {role}. Rolling back.")
                snapshot.rollback()
                err_msg = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
                raise RuntimeError(
                    f"Prompt mutation rollback triggered due to test failure: {err_msg}"
                ) from exc


async def async_main(*params: str) -> None:
    """Async CLI entrypoint for SkillOpt adapter."""
    parser = argparse.ArgumentParser(
        description="Microsoft SkillOpt Self-Learning Adaptation for Antigravity"
    )
    parser.add_argument(
        "--evaluate-telemetry", action="store_true", help="Evaluate conversation event trajectories"
    )
    parser.add_argument(
        "--optimize-skills", action="store_true", help="Run prompt optimization loop"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run evaluation without persisting prompt mutations"
    )

    args = parser.parse_args(list(params) if params else [])

    adapter = SkillOptAdapter()

    if args.evaluate_telemetry or not args.optimize_skills:
        stats = adapter.evaluate_trajectories()
        print(
            f"SkillOpt Trajectory Evaluation: Total Events={stats['total_events']}, Failed Tools={stats['failed_tools_count']}, Error Rate={stats['error_rate']}"
        )

    if args.optimize_skills:
        res = adapter.optimize_prompts(dry_run=args.dry_run)
        print(f"SkillOpt Prompt Optimization Result: Status={res['status']}")


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
