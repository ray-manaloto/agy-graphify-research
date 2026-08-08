# Original User Request

## Initial Request — 2026-07-30T20:36:51-05:00

<USER_REQUEST>
Independent multi-agent adversarial QA, verification, and victory audit across Phase 2 (SkillOpt Prompt Mutation & OpenTelemetry Tracing) and the Autonomous Auto-Succession Engine design.

Working directory: /Users/rmanaloto/agy-graphify-research
Integrity mode: development

## Requirements

### R1. Adversarial Codebase & Schema Inspection
Conduct adversarial inspection of updated codebase files (src/agy_graphify/orchestration.py, src/agy_graphify/skillopt.py, src/agy_graphify/telemetry.py, src/agy_graphify/context_manager.py) for edge-case failures, unhandled exceptions, and AST-level integrity.

### R2. Automated Verification & Regression Testing
Execute full test and verification pipelines (.venv/bin/python -m pytest, uv run --active --no-sync agy-task harness-validate, uv run --active --no-sync agy-verify, uv run python3 -m agy_graphify.okf docs).

## Acceptance Criteria

### Automated Verification Criteria
- [ ] .venv/bin/python -m pytest passes 100% of unit tests (25/25 tests)
- [ ] uv run --active --no-sync agy-task harness-validate completes all 4 pipeline steps successfully
- [ ] uv run --active --no-sync agy-verify confirms zero .sh shell scripts and clean AST forensic audit
- [ ] OKF validator (uv run python3 -m agy_graphify.okf docs) passes all documentation and LESSONS.md checks
- [ ] Adversarial QA Reviewer and Independent Victory Auditor issue verdict of VICTORY CONFIRMED
</USER_REQUEST>

## Follow-up — 2026-08-07T12:00:32Z

<USER_REQUEST>
Consolidate repository source ingestion and Colibri knowledge graph extraction into `graphify_pipeline` (`.agents/skills/graphify_pipeline/SKILL.md`) as the single canonical master skill, eliminating duplicate skills while preserving 100% of source parsing, deduplication, differential tracking, and extraction features, verified repeatably via unit test suite.

Working directory: `/Users/rmanaloto/agy-graphify-research`
Integrity mode: development

## Requirements

### R1. Single Canonical Master Skill (`graphify_pipeline`)
Ensure `.agents/skills/graphify_pipeline/SKILL.md` is the single master skill containing complete source parsing (GitHub URLs, Crates.io packages), deduplication against `config/sources.json`, Git SHA differential tracking (`uv run agy-task update-all-sources`), and local zero-token Colibri graph extraction (`uv run agy-task colibri-graphify`).

### R2. Zero Duplicate Symlinks or Broken Skills
Verify `.agents/skills/` contains zero duplicate or broken symlinks (`visual-edit`, `visual-plan`, `visual-recap`), retaining only clean canonical underscore directories.

### R3. Feature Retention & Skill Deduplication Test Suite
Verify `tests/test_skill_deduplication.py` includes repeatable unit test assertions for:
- Zero duplicate or broken symlink files.
- Valid YAML frontmatter headers across all skill `SKILL.md` files.
- Feature keyword presence (`update-all-sources`, `colibri-graphify`, `Deduplicate`, `graphify-out/graph.json`, `GRAPH_REPORT.md`) in `graphify_pipeline/SKILL.md`.

## Verification Resources

- Master Pipeline Skill: `.agents/skills/graphify_pipeline/SKILL.md`
- Skills Directory: `.agents/skills/`
- Test Suite: `tests/test_skill_deduplication.py`

## Acceptance Criteria

- [ ] `.agents/skills/` contains zero duplicate or broken symlinks.
- [ ] `graphify_pipeline` serves as the single master skill retaining 100% of ingestion and extraction features.
- [ ] 124/124 unit tests pass (`uv run pytest`).
- [ ] `ALLOW_MAIN_COMMIT=1 uv run agy-verify` returns `decision: allow`.
</USER_REQUEST>

## Follow-up — 2026-08-07T22:18:21Z

<USER_REQUEST>
Refactor and create the Graphify sources directory layout across the workspace:

1. Create canonical `raw/` multi-modal directory layout at workspace root:
   - `raw/papers/.gitkeep` (for `.pdf` academic papers & books)
   - `raw/media/.gitkeep` (for `.mp4`, `.mp3`, `.m4a`, `.wav` video/audio)
   - `raw/web/.gitkeep` (for scraped web pages and HTML/markdown articles)
   - `raw/images/.gitkeep` (for `.png`, `.jpg`, `.svg` images & diagrams)

2. Update `config/sources.json`:
   - Add explicit source path mapping:
     ```json
     {
       "version": "1.1.0",
       "updated_at": "2026-08-07T22:18:00Z",
       "manifest_source": "graphify-out/extended_repo_manifest.json",
       "sources": {
         "git_repositories": "repos/",
         "raw_papers": "raw/papers/",
         "raw_media": "raw/media/",
         "raw_web": "raw/web/",
         "raw_images": "raw/images/"
       }
     }
     ```

3. Update `src/agy_graphify/source_registry.py` and `src/agy_graphify/tasks.py`:
   - Enhance `SourceRegistryManager` to scan `raw/` multi-modal subdirectories alongside `repos/`.
   - Update `update-all-sources` action to verify and auto-create `raw/` subdirectories.

4. Add unit tests in `tests/test_source_registry.py` and update `tests/test_workspace_layout_standards.py`.

5. Run full test suite (`uv run pytest`), verify `ALLOW_MAIN_COMMIT=1 uv run agy-verify`, and create PR to squash-merge into `main`.

Working directory: `/Users/rmanaloto/agy-graphify-research`
Integrity mode: development

## Acceptance Criteria
- [ ] `raw/` directory layout created and tracked in git.
- [ ] `config/sources.json` registers multi-modal sources.
- [ ] `SourceRegistryManager` scans `raw/` multi-modal files.
- [ ] 130+ unit tests pass (`uv run pytest`).
- [ ] `ALLOW_MAIN_COMMIT=1 uv run agy-verify` returns `decision: allow`.
- [ ] Independent Victory Auditor issues `VICTORY CONFIRMED`.
</USER_REQUEST>
