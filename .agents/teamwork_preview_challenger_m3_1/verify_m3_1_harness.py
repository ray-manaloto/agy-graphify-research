"""Empirical Stress Test Harness for teamwork_preview_challenger_m3_1.

Tests:
1. Multi-run sequential execution continuity of Colibri benchmark script.
2. MemoryStoreAdapter tail hash seeding edge cases (empty file, trailing newlines, corrupt JSON, missing causal_hash, non-dict JSON).
3. OKF Validator edge case matrix (doc_id, version, type, status, SKILL.md, missing headings, malformed YAML).
"""

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from agy_graphify.telemetry import CausalTelemetryEvent, MemoryStoreAdapter
from agy_graphify.okf import OKFValidator
from agy_graphify.models.verification_schema import Decision


def test_colibri_multi_run_hash_chain(tmp_path: Path) -> dict:
    """Stress test multi-execution of colibri benchmark workflow over 5 runs in a single process & across process-like re-instantiations."""
    from scripts.execute_colibri_benchmark import execute_colibri_workflow

    causal_file = tmp_path / ".gemini" / "telemetry" / "causal_events.jsonl"
    
    run_results = []
    total_events_expected = 0

    for run_idx in range(1, 6):
        # Run workflow targeting tmp_path
        res = asyncio.run(execute_colibri_workflow(project_dir=tmp_path))
        lines = [l for l in causal_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        total_events_expected += 12
        assert len(lines) == total_events_expected, f"Run {run_idx}: Expected {total_events_expected} lines, got {len(lines)}"

        # Verify full line-by-line SHA-256 chain continuity from line 0 to line N-1
        prev_hash = ""
        for line_idx, line in enumerate(lines):
            raw = json.loads(line)
            event = CausalTelemetryEvent.model_validate(raw)
            expected_hash = event.compute_causal_hash(prev_hash)
            assert event.causal_hash == expected_hash, (
                f"Run {run_idx}, Line {line_idx} mismatch! Expected {expected_hash}, got {event.causal_hash}"
            )
            prev_hash = event.causal_hash

        run_results.append({
            "run": run_idx,
            "total_lines": len(lines),
            "tail_hash": prev_hash,
            "chain_valid": True,
        })

    return {
        "status": "PASS",
        "runs_executed": 5,
        "total_events_verified": total_events_expected,
        "run_details": run_results,
    }


def test_tail_hash_seeding_edge_cases(tmp_path: Path) -> dict:
    """Test MemoryStoreAdapter _last_hash seeding across edge cases."""
    results = {}
    
    # Case 1: Non-existent file
    d1 = tmp_path / "case1"
    d1.mkdir()
    adapter1 = MemoryStoreAdapter(output_dir=d1)
    results["non_existent_file"] = (adapter1._last_hash == "")

    # Case 2: Empty file
    d2 = tmp_path / "case2"
    d2.mkdir()
    f2 = d2 / "causal_events.jsonl"
    f2.write_text("", encoding="utf-8")
    adapter2 = MemoryStoreAdapter(output_dir=d2)
    results["empty_file"] = (adapter2._last_hash == "")

    # Case 3: Trailing blank lines after valid event
    d3 = tmp_path / "case3"
    d3.mkdir()
    f3 = d3 / "causal_events.jsonl"
    ev = CausalTelemetryEvent(
        event_id="e3", conversation_id="c3", step_index=0, event_type="INIT"
    )
    ev.causal_hash = ev.compute_causal_hash("")
    f3.write_text(ev.model_dump_json() + "\n\n\n   \n", encoding="utf-8")
    adapter3 = MemoryStoreAdapter(output_dir=d3)
    results["trailing_blank_lines"] = (adapter3._last_hash == ev.causal_hash)

    # Case 4: Corrupt JSON on last line
    d4 = tmp_path / "case4"
    d4.mkdir()
    f4 = d4 / "causal_events.jsonl"
    f4.write_text('{"event_id": "bad", "causal_hash": "corrupt', encoding="utf-8")
    adapter4 = MemoryStoreAdapter(output_dir=d4)
    results["corrupt_json_last_line"] = (adapter4._last_hash == "")

    # Case 5: Missing causal_hash key in last line
    d5 = tmp_path / "case5"
    d5.mkdir()
    f5 = d5 / "causal_events.jsonl"
    f5.write_text('{"event_id": "no_hash"}', encoding="utf-8")
    adapter5 = MemoryStoreAdapter(output_dir=d5)
    results["missing_causal_hash_key"] = (adapter5._last_hash == "")

    # Case 6: Non-dict JSON on last line
    d6 = tmp_path / "case6"
    d6.mkdir()
    f6 = d6 / "causal_events.jsonl"
    f6.write_text('[1, 2, 3]', encoding="utf-8")
    adapter6 = MemoryStoreAdapter(output_dir=d6)
    results["non_dict_json_last_line"] = (adapter6._last_hash == "")

    # Case 7: Appending to existing valid tail hash
    d7 = tmp_path / "case7"
    d7.mkdir()
    adapter7_first = MemoryStoreAdapter(output_dir=d7)
    ev_a = CausalTelemetryEvent(event_id="eA", conversation_id="cA", step_index=0)
    adapter7_first.append_causal_event(ev_a)
    hash_a = ev_a.causal_hash

    # Re-instantiate MemoryStoreAdapter to simulate process restart
    adapter7_second = MemoryStoreAdapter(output_dir=d7)
    results["reinit_seeded_from_previous_run"] = (adapter7_second._last_hash == hash_a)
    
    ev_b = CausalTelemetryEvent(event_id="eB", conversation_id="cA", step_index=1)
    adapter7_second.append_causal_event(ev_b)
    
    # Read file and verify full hash chain
    lines = (d7 / "causal_events.jsonl").read_text(encoding="utf-8").splitlines()
    raw_a = json.loads(lines[0])
    raw_b = json.loads(lines[1])
    ev_a_read = CausalTelemetryEvent.model_validate(raw_a)
    ev_b_read = CausalTelemetryEvent.model_validate(raw_b)
    
    chain_ok = (
        ev_a_read.causal_hash == ev_a_read.compute_causal_hash("") and
        ev_b_read.causal_hash == ev_b_read.compute_causal_hash(ev_a_read.causal_hash)
    )
    results["multi_process_hash_chain_continuation"] = chain_ok

    all_passed = all(results.values())
    return {
        "status": "PASS" if all_passed else "FAIL",
        "details": results,
    }


def test_okf_validator_edge_cases(tmp_path: Path) -> dict:
    """Test OKFValidator against various doc edge cases."""
    validator = OKFValidator(target_dir=tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    edge_cases = []

    # 1. Missing YAML frontmatter header
    f1 = docs_dir / "doc1.md"
    f1.write_text("Title without frontmatter\n\n## Overview\nSome content", encoding="utf-8")
    issues1 = asyncio.run(validator.validate_file(f1))
    edge_cases.append({
        "case": "Missing YAML header ---",
        "expected_issue": True,
        "actual_issues": issues1,
        "passed": len(issues1) > 0 and "Missing YAML frontmatter header" in issues1[0],
    })

    # 2. Malformed frontmatter (only 1 separator)
    f2 = docs_dir / "doc2.md"
    f2.write_text("---\ntitle: Test\nbody text", encoding="utf-8")
    issues2 = asyncio.run(validator.validate_file(f2))
    edge_cases.append({
        "case": "Malformed YAML frontmatter",
        "expected_issue": True,
        "actual_issues": issues2,
        "passed": len(issues2) > 0 and "Malformed YAML frontmatter" in issues2[0],
    })

    # 3. Invalid doc_id (pattern: ^okf-[a-z0-9-]+$)
    f3 = docs_dir / "doc3.md"
    f3.write_text("---\ntitle: Test\ndoc_id: INVALID_ID\nversion: 1.0.0\ntype: report\n---\n\n## Overview\nContent", encoding="utf-8")
    issues3 = asyncio.run(validator.validate_file(f3))
    edge_cases.append({
        "case": "Invalid doc_id regex",
        "expected_issue": True,
        "actual_issues": issues3,
        "passed": any("doc_id" in iss for iss in issues3),
    })

    # 4. Invalid version (pattern: ^\d+\.\d+\.\d+$)
    f4 = docs_dir / "doc4.md"
    f4.write_text("---\ntitle: Test\ndoc_id: okf-test-doc\nversion: 1.0\ntype: report\n---\n\n## Overview\nContent", encoding="utf-8")
    issues4 = asyncio.run(validator.validate_file(f4))
    edge_cases.append({
        "case": "Invalid semver pattern",
        "expected_issue": True,
        "actual_issues": issues4,
        "passed": any("version" in iss for iss in issues4),
    })

    # 5. Invalid type enum
    f5 = docs_dir / "doc5.md"
    f5.write_text("---\ntitle: Test\ndoc_id: okf-test-doc\nversion: 1.0.0\ntype: blog_post\n---\n\n## Overview\nContent", encoding="utf-8")
    issues5 = asyncio.run(validator.validate_file(f5))
    edge_cases.append({
        "case": "Invalid type enum",
        "expected_issue": True,
        "actual_issues": issues5,
        "passed": any("type" in iss for iss in issues5),
    })

    # 6. Missing section heading
    f6 = docs_dir / "doc6.md"
    f6.write_text("---\ntitle: Test\ndoc_id: okf-test-doc\nversion: 1.0.0\ntype: report\n---\n\n## Summary\nContent", encoding="utf-8")
    issues6 = asyncio.run(validator.validate_file(f6))
    edge_cases.append({
        "case": "Missing required section header (Overview/Context/Learned Remediation Rules)",
        "expected_issue": True,
        "actual_issues": issues6,
        "passed": any("Missing required section" in iss for iss in issues6),
    })

    # 7. SKILL.md missing description
    f7 = docs_dir / "SKILL.md"
    f7.write_text("---\nname: my-skill\n---\n\n## Overview\nContent", encoding="utf-8")
    issues7 = asyncio.run(validator.validate_file(f7))
    edge_cases.append({
        "case": "SKILL.md missing description",
        "expected_issue": True,
        "actual_issues": issues7,
        "passed": any("Missing required skill frontmatter field" in iss for iss in issues7),
    })

    # 8. Fully Valid Standard OKF Document
    f8 = docs_dir / "doc8.md"
    f8.write_text("---\ntitle: Valid Document\ndoc_id: okf-valid-doc\nversion: 1.0.0\ntype: report\nstatus: approved\nauthor: test_author\n---\n\n## Overview\nThis is a valid document body.", encoding="utf-8")
    issues8 = asyncio.run(validator.validate_file(f8))
    edge_cases.append({
        "case": "Valid OKF standard document",
        "expected_issue": False,
        "actual_issues": issues8,
        "passed": len(issues8) == 0,
    })

    all_passed = all(ec["passed"] for ec in edge_cases)
    return {
        "status": "PASS" if all_passed else "FAIL",
        "total_cases": len(edge_cases),
        "passed_cases": sum(1 for ec in edge_cases if ec["passed"]),
        "cases": edge_cases,
    }


def main():
    print("=== EMPIRICAL STRESS TEST HARNESS (preview_m3_1) ===")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        print("\n1. Multi-Run Colibri Benchmark Causal Hash Chaining Test...")
        res_multi = test_colibri_multi_run_hash_chain(tmp_path)
        print(f"   Status: {res_multi['status']} ({res_multi['runs_executed']} runs, {res_multi['total_events_verified']} events verified)")

        print("\n2. Tail Hash Seeding Edge Cases Test...")
        res_tail = test_tail_hash_seeding_edge_cases(tmp_path)
        print(f"   Status: {res_tail['status']}")
        for k, v in res_tail['details'].items():
            print(f"   - {k}: {'PASS' if v else 'FAIL'}")

        print("\n3. OKF Validator Edge Cases Test...")
        res_okf = test_okf_validator_edge_cases(tmp_path)
        print(f"   Status: {res_okf['status']} ({res_okf['passed_cases']}/{res_okf['total_cases']} cases passed)")
        for c in res_okf['cases']:
            print(f"   - {c['case']}: {'PASS' if c['passed'] else 'FAIL'}")
            if not c['passed']:
                print(f"     Issues: {c['actual_issues']}")

    print("\n=== STRESS TEST COMPLETED ===")


if __name__ == "__main__":
    main()
