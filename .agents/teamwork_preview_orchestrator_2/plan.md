# Implementation Plan — Graphify Sources Directory Layout & Multi-Modal Ingestion

## Overview
Refactor and create the canonical Graphify sources directory layout (`raw/` multi-modal subdirectories), update `config/sources.json`, enhance `SourceRegistryManager` and `update-all-sources` CLI task, update and write comprehensive unit tests, verify environment compliance, and create/merge Pull Request.

## Proposed Decomposition (Milestones)

### Step 0: Initial Codebase Survey
- Spawn `teamwork_preview_explorer` subagents to analyze existing implementation in:
  - `config/sources.json`
  - `src/agy_graphify/source_registry.py`
  - `src/agy_graphify/tasks.py`
  - `tests/test_source_registry.py`
  - `tests/test_workspace_layout_standards.py`
  - `docs/graphify_sources_proposal_architecture.md`

### Milestone 1: Raw Directory Layout & Gitkeeps
- Create canonical `raw/` directory structure with `.gitkeep` files:
  - `raw/papers/.gitkeep`
  - `raw/media/.gitkeep`
  - `raw/web/.gitkeep`
  - `raw/images/.gitkeep`

### Milestone 2: Sources JSON Configuration Update
- Update `config/sources.json` to version 1.1.0 with explicit source path mapping for `git_repositories`, `raw_papers`, `raw_media`, `raw_web`, `raw_images`.

### Milestone 3: Source Registry Manager & Task Enhancement
- Enhance `SourceRegistryManager` in `src/agy_graphify/source_registry.py` to scan `raw/` multi-modal subdirectories alongside `repos/`.
- Update `update-all-sources` action in `src/agy_graphify/tasks.py` to auto-create and verify `raw/` subdirectories.

### Milestone 4: Verification, Testing, and PR Creation
- Add unit tests in `tests/test_source_registry.py`.
- Update `tests/test_workspace_layout_standards.py`.
- Run full pytest test suite (`uv run pytest`).
- Verify `ALLOW_MAIN_COMMIT=1 uv run agy-verify`.
- Create PR to squash-merge into `main` and clean up.

## Verification & Audit Gates
Each milestone requires:
- Implementation worker report
- Independent code reviewers (verdict: APPROVE)
- Challenger verification (verdict: APPROVE)
- Forensic Integrity Auditor verification (verdict: CLEAN)
