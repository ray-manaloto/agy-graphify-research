# Orchestration Plan: Skill Consolidation & Verification

## Objective
Consolidate repository source ingestion and Colibri knowledge graph extraction into `graphify_pipeline` (`.agents/skills/graphify_pipeline/SKILL.md`) as the single canonical master skill, eliminate duplicate or broken symlinks in `.agents/skills/`, and verify via `tests/test_skill_deduplication.py`, full unit test suite (124/124 tests pass), and `ALLOW_MAIN_COMMIT=1 uv run agy-verify`.

## Architecture & Scope
- Master Skill: `.agents/skills/graphify_pipeline/SKILL.md`
- Skills Directory: `.agents/skills/`
- Test Suite: `tests/test_skill_deduplication.py`

## Milestones
1. **Step 0: Survey & Discovery** (3 Explorers)
   - Map existing skills in `.agents/skills/` (including `graphify_pipeline`, `repo_ingest`, `colibri_graphify`, `colibri_benchmark`, etc.)
   - Identify duplicate/broken symlinks (`visual-edit`, `visual-plan`, `visual-recap`, etc.)
   - Inspect existing `tests/test_skill_deduplication.py` and current pytest results.
2. **Milestone 1: Master Skill Consolidation** (R1)
   - Ensure `.agents/skills/graphify_pipeline/SKILL.md` incorporates complete parsing (GitHub URLs, Crates.io packages), deduplication against `config/sources.json`, Git SHA differential tracking (`uv run agy-task update-all-sources`), and local zero-token Colibri graph extraction (`uv run agy-task colibri-graphify`).
3. **Milestone 2: Duplicate Symlink & Skill Cleanup** (R2)
   - Remove duplicate/broken symlinks (`visual-edit`, `visual-plan`, `visual-recap`), retaining only clean canonical underscore directories.
4. **Milestone 3: Unit Test Suite Enhancement & Verification** (R3 & Acceptance)
   - Update `tests/test_skill_deduplication.py` with assertions for zero broken/duplicate symlinks, valid YAML frontmatter, and feature keyword presence.
   - Run unit test suite (124/124 passing) and `ALLOW_MAIN_COMMIT=1 uv run agy-verify` returning `decision: allow`.
