# Feature Retention & Skill Deduplication Test Suite Analysis (R3)

## Overview
This report documents the detailed investigation of Requirement R3 (Feature Retention & Skill Deduplication Test Suite in `tests/test_skill_deduplication.py`) and the project verification environment for `agy-graphify-research`.

---

## 1. Unit Test Assertion Analysis (`tests/test_skill_deduplication.py`)

The test suite in `tests/test_skill_deduplication.py` contains 3 primary unit test functions designed to enforce skill deduplication, directory integrity, YAML frontmatter compliance, and feature keyword retention in the master skill `graphify_pipeline/SKILL.md`.

### Assertion 1: Symlink & Duplicate Directory Removal (`test_no_duplicate_skill_symlinks`)
- **Location**: `tests/test_skill_deduplication.py:7-16`
- **Assertion Logic**:
  ```python
  def test_no_duplicate_skill_symlinks() -> None:
      skills_dir = Path(".agents/skills")
      assert skills_dir.exists(), ".agents/skills directory missing"

      disallowed_symlinks = ["visual-edit", "visual-plan", "visual-recap", "repo_ingest"]
      for symlink_name in disallowed_symlinks:
          target = skills_dir / symlink_name
          assert not target.exists(), f"Duplicate skill file/symlink '{symlink_name}' still exists in .agents/skills!"
  ```
- **Findings**:
  - The `.agents/skills` directory contains 11 canonical skill directories using underscore naming convention:
    1. `colibri_benchmark`
    2. `dag`
    3. `graphify`
    4. `graphify_pipeline`
    5. `last30days`
    6. `orchestration_harness`
    7. `pr`
    8. `resume`
    9. `visual_edit`
    10. `visual_plan`
    11. `visual_recap`
  - The disallowed entries (`visual-edit`, `visual-plan`, `visual-recap`, `repo_ingest`) do not exist in `.agents/skills`.
  - Inspection via `ls -la .agents/skills` confirms zero duplicate hyphenated symlinks or broken symlinks exist.

### Assertion 2: Skill YAML Frontmatter Validation (`test_canonical_skills_contain_valid_frontmatter`)
- **Location**: `tests/test_skill_deduplication.py:18-30`
- **Assertion Logic**:
  ```python
  def test_canonical_skills_contain_valid_frontmatter() -> None:
      skills_dir = Path(".agents/skills")
      assert skills_dir.exists()

      skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
      assert len(skill_dirs) > 0, "No skill directories found"

      for skill_dir in skill_dirs:
          skill_file = skill_dir / "SKILL.md"
          assert skill_file.exists(), f"Skill directory '{skill_dir.name}' missing SKILL.md!"
          content = skill_file.read_text(encoding="utf-8")
          assert content.startswith("---"), f"{skill_file} missing YAML frontmatter header ('---')"
  ```
- **Findings**:
  - Dynamically scans all non-hidden directories under `.agents/skills/`.
  - Asserts every directory contains a `SKILL.md` file.
  - Asserts every `SKILL.md` file begins with the `---` YAML frontmatter marker.
  - All 11 skills pass this assertion cleanly.

### Assertion 3: Master Skill Feature Keyword Retention (`test_master_graphify_pipeline_retains_all_features`)
- **Location**: `tests/test_skill_deduplication.py:32-46`
- **Assertion Logic**:
  ```python
  def test_master_graphify_pipeline_retains_all_features() -> None:
      pipeline_file = Path(".agents/skills/graphify_pipeline/SKILL.md")
      assert pipeline_file.exists(), "graphify_pipeline/SKILL.md missing"
      content = pipeline_file.read_text(encoding="utf-8")

      required_keywords = [
          "update-all-sources",
          "colibri-graphify",
          "Deduplicate",
          "graphify-out/graph.json",
          "graphify-out/GRAPH_REPORT.md",
      ]
      for kw in required_keywords:
          assert kw in content, f"Master graphify_pipeline skill missing critical feature keyword '{kw}'"
  ```
- **Findings & Keyword Mapping in `.agents/skills/graphify_pipeline/SKILL.md`**:
  1. `update-all-sources` -> Line 24: `uv run agy-task update-all-sources`
  2. `colibri-graphify` -> Line 33: `uv run agy-task colibri-graphify`
  3. `Deduplicate` -> Line 19: `Deduplicate target URLs against existing registered repositories in config/sources.json.`
  4. `graphify-out/graph.json` -> Line 38: `Ensure that both graphify-out/graph.json...`
  5. `graphify-out/GRAPH_REPORT.md` -> Line 38: `...and graphify-out/GRAPH_REPORT.md are populated properly...`
- All 5 required feature keywords are present and verified in `graphify_pipeline/SKILL.md`.

---

## 2. Verification Environment Assessment

1. **Targeted Pytest**: `uv run pytest tests/test_skill_deduplication.py` executes in 0.01s with 3/3 passed tests (100%).
2. **Full Pytest Suite**: `uv run pytest` collects 124 unit test items across 25 test files in `tests/`.
3. **Environment Verifier (`agy-verify`)**:
   - Entrypoint: `src/agy_graphify/verify.py` (`EnvironmentVerifier` & `IntegrityAuditor`).
   - Command: `ALLOW_MAIN_COMMIT=1 uv run agy-verify`.
   - Checks performed:
     - Project & Global Isolation (`.gemini/settings.json`, `.gemini/rules`)
     - Toolchain Pinning (`.mise.toml` with pinned versions for python, uv, ruff, ty, hk, fnox, pkl, taplo, gh)
     - Zero Shell Script Enforcement (scans core codebase for `*.sh` files)
     - AST Forensic Audit (scans `src/` AST for hardcoded string returns >50 chars, prohibited shell calls, reinvented JSON/logging utilities)
     - Branch Protection (`git branch --show-current`, overridden by `ALLOW_MAIN_COMMIT=1`)
     - Repository Manifest Audit (`graphify-out/extended_repo_manifest.json` count vs `repos/`)
     - Live PyPI & GitHub release checks
     - Fail-Fast Watchdog Scan of `.gemini/telemetry/universal.log`.
   - Note on Fail-Fast Watchdog: During unit test runs, test suites intentionally trigger error paths or corrupted test states which log warnings/errors to `universal.log`. When `universal.log` is clean, `agy-verify` returns `{"decision": "allow", ...}`.

---

## Summary Matrix

| Requirement Component | Test Function | Target Path | Verified Status |
|---|---|---|---|
| Symlink / Duplicate Cleanup | `test_no_duplicate_skill_symlinks` | `.agents/skills/` | PASS (11 canonical underscore dirs) |
| YAML Frontmatter Headers | `test_canonical_skills_contain_valid_frontmatter` | `.agents/skills/*/SKILL.md` | PASS (All 11 SKILL.md start with `---`) |
| Feature Keywords Retention | `test_master_graphify_pipeline_retains_all_features` | `.agents/skills/graphify_pipeline/SKILL.md` | PASS (All 5 keywords present) |
| Dedicated Test Execution | `uv run pytest tests/test_skill_deduplication.py` | `tests/test_skill_deduplication.py` | PASS (3/3 tests) |
