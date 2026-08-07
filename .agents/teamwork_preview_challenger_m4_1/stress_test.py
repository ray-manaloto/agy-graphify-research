"""Empirical Stress Test Harness for ContextManagerEngine & SkillSnapshotContext."""

import asyncio
import math
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Add project src to python path if needed
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agy_graphify.context_manager import ContextManagerEngine, ContextMetrics
from agy_graphify.skillopt import SkillSnapshotContext


def log_result(test_name: str, passed: bool, detail: str) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {test_name}: {detail}")


async def stress_test_context_manager():
    print("\n=== STRESS TESTING ContextManagerEngine.evaluate_context ===")
    engine = ContextManagerEngine()

    # 1. Edge Case: Negative tokens
    test_cases_negative = [-1, -100, -999999, -sys.maxsize]
    for neg_val in test_cases_negative:
        metrics = await engine.evaluate_context(estimated_tokens=neg_val)
        passed = (
            metrics.estimated_context_tokens == 0
            and metrics.utilization_percentage == 0.0
            and not metrics.requires_subagent_delegation
            and metrics.recommended_model == "flash"
        )
        log_result(f"Negative Tokens ({neg_val})", passed, f"Metrics: {metrics.model_dump()}")

    # 2. Edge Case: Zero & Baseline tokens
    metrics_zero = await engine.evaluate_context(estimated_tokens=0)
    log_result("Zero Tokens (0)", metrics_zero.utilization_percentage == 0.0, f"Metrics: {metrics_zero.model_dump()}")

    # 3. Threshold Boundary Tests (40% delegation, 45% model recommendation)
    # limit = 200,000
    # 40% threshold = 80,000 tokens
    # 45% threshold = 90,000 tokens
    b_79999 = await engine.evaluate_context(estimated_tokens=79999)
    passed_79999 = not b_79999.requires_subagent_delegation and b_79999.recommended_model == "flash"
    log_result("Boundary 79,999 tokens (39.9995%)", passed_79999, f"Delegation={b_79999.requires_subagent_delegation}, Model={b_79999.recommended_model}, Util={b_79999.utilization_percentage:.4f}%")

    b_80000 = await engine.evaluate_context(estimated_tokens=80000)
    passed_80000 = b_80000.requires_subagent_delegation and b_80000.recommended_model == "flash"
    log_result("Boundary 80,000 tokens (40.0%)", passed_80000, f"Delegation={b_80000.requires_subagent_delegation}, Model={b_80000.recommended_model}, Util={b_80000.utilization_percentage:.4f}%")

    b_89999 = await engine.evaluate_context(estimated_tokens=89999)
    passed_89999 = b_89999.requires_subagent_delegation and b_89999.recommended_model == "flash"
    log_result("Boundary 89,999 tokens (44.9995%)", passed_89999, f"Delegation={b_89999.requires_subagent_delegation}, Model={b_89999.recommended_model}, Util={b_89999.utilization_percentage:.4f}%")

    b_90000 = await engine.evaluate_context(estimated_tokens=90000)
    passed_90000 = b_90000.requires_subagent_delegation and b_90000.recommended_model == "pro"
    log_result("Boundary 90,000 tokens (45.0%)", passed_90000, f"Delegation={b_90000.requires_subagent_delegation}, Model={b_90000.recommended_model}, Util={b_90000.utilization_percentage:.4f}%")

    # 4. Edge Case: Overflow tokens
    overflow_cases = [200000, 200001, 500000, 1000000, 10**9, sys.maxsize]
    for over_val in overflow_cases:
        metrics = await engine.evaluate_context(estimated_tokens=over_val)
        passed = (
            metrics.estimated_context_tokens == over_val
            and metrics.utilization_percentage == 100.0
            and metrics.requires_subagent_delegation is True
            and metrics.recommended_model == "pro"
        )
        log_result(f"Overflow Tokens ({over_val})", passed, f"Util={metrics.utilization_percentage}%, Delegation={metrics.requires_subagent_delegation}")

    # 5. Invalid / Non-standard Types
    try:
        # Float evaluation
        flt_metrics = await engine.evaluate_context(estimated_tokens=85000.5) # type: ignore
        log_result("Float token value (85000.5)", True, f"Util={flt_metrics.utilization_percentage}%")
    except Exception as exc:
        log_result("Float token value", False, f"Raised exception: {exc}")

    # 6. High Concurrency Performance Stress Test (10,000 async calls)
    t0 = time.perf_counter()
    tasks = [engine.evaluate_context(estimated_tokens=i * 10) for i in range(10000)]
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - t0
    log_result(
        "High Concurrency Stress (10,000 async evaluations)",
        len(results) == 10000 and elapsed < 2.0,
        f"Completed 10,000 calls in {elapsed:.4f} seconds ({len(results)/elapsed:.0f} ops/sec)"
    )


def stress_test_skill_snapshot_context():
    print("\n=== STRESS TESTING SkillSnapshotContext Path Resolution & Rollback ===")

    # Test Setup in temp directory
    with tempfile.TemporaryDirectory(prefix="test_skill_snapshot_") as tmp_root_str:
        tmp_root = Path(tmp_root_str).resolve()
        proj_dir = tmp_root / "test_project"
        proj_dir.mkdir(parents=True)

        agents_skills = proj_dir / ".agents" / "skills"
        gemini_skills = proj_dir / ".gemini" / "skills"

        agents_skills.mkdir(parents=True)
        (agents_skills / "skill1.txt").write_text("v1_agents", encoding="utf-8")

        # 1. Normal backup and rollback when exception raised
        try:
            with SkillSnapshotContext(project_dir=proj_dir) as snapshot:
                # Modify existing file and add new file
                (agents_skills / "skill1.txt").write_text("v2_modified", encoding="utf-8")
                (agents_skills / "skill2.txt").write_text("new_file", encoding="utf-8")
                gemini_skills.mkdir(parents=True)
                (gemini_skills / "gem_skill.txt").write_text("created_in_context", encoding="utf-8")
                raise RuntimeError("Simulated failure inside skill optimization block")
        except RuntimeError:
            pass

        # Check if rollback restored original state
        v1_restored = (agents_skills / "skill1.txt").read_text(encoding="utf-8") == "v1_agents"
        skill2_removed = not (agents_skills / "skill2.txt").exists()
        gemini_cleaned = not gemini_skills.exists()
        log_result(
            "Rollback on Exception",
            v1_restored and skill2_removed and gemini_cleaned,
            f"v1 restored: {v1_restored}, skill2 removed: {skill2_removed}, gemini cleaned: {gemini_cleaned}"
        )

        # 2. Path Resolution Edge Case: External Skill Directory (Outside project_dir)
        # Create an external directory outside proj_dir
        ext_dir = tmp_root / "external_skills_dir" / "skills"
        ext_dir.mkdir(parents=True)
        (ext_dir / "external_skill.txt").write_text("ext_v1", encoding="utf-8")

        # Create another skill dir with the SAME name ("skills") in another external path
        ext_dir_2 = tmp_root / "external_skills_dir_2" / "skills"
        ext_dir_2.mkdir(parents=True)
        (ext_dir_2 / "ext2_skill.txt").write_text("ext2_v1", encoding="utf-8")

        ctx = SkillSnapshotContext(project_dir=proj_dir)
        # Manually set skills_dirs to point to external paths with identical final name ("skills")
        ctx.skills_dirs = [ext_dir, ext_dir_2]

        collision_detected = False
        try:
            with ctx:
                # Inspect temp_dir structure
                snapshot_children = list(ctx.temp_dir.iterdir())
                # If rel_path fallback to Path(s_dir.name) occurs for both, both map to temp_dir / "skills"!
                if len(snapshot_children) < 2:
                    collision_detected = True
                    print(f"  [DISCOVERY] Path resolution collision detected! Snapshot dir only has {len(snapshot_children)} items: {[c.name for c in snapshot_children]}")
        except Exception as exc:
            print(f"  [DISCOVERY] Snapshot context exception with external dirs: {exc}")

        log_result(
            "External Directory Name Collision Vulnerability Test",
            not collision_detected,
            f"Collision detected: {collision_detected} (both external skill paths named 'skills' collapsed to same snapshot folder)"
        )

        # 3. Symlink path resolution test
        symlink_skills = proj_dir / "symlinked_skills"
        real_target = tmp_root / "real_skills_target"
        real_target.mkdir(parents=True)
        (real_target / "sym_skill.txt").write_text("sym_v1", encoding="utf-8")
        try:
            symlink_skills.symlink_to(real_target)
            ctx_sym = SkillSnapshotContext(project_dir=proj_dir)
            ctx_sym.skills_dirs = [symlink_skills]
            with ctx_sym:
                (real_target / "sym_skill.txt").write_text("sym_v2_modified", encoding="utf-8")
                raise ValueError("Symlink test failure trigger")
        except ValueError:
            pass
        except Exception as exc:
            print(f"  [DISCOVERY] Symlink handling error: {exc}")

        sym_restored = (real_target / "sym_skill.txt").read_text(encoding="utf-8") == "sym_v1"
        log_result(
            "Symlinked Skill Directory Resolution & Rollback",
            sym_restored,
            f"Content after rollback: '{real_target / 'sym_skill.txt'}'"
        )


async def main():
    await stress_test_context_manager()
    stress_test_skill_snapshot_context()


if __name__ == "__main__":
    asyncio.run(main())
