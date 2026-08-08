# Master Plan: Verification of Multi-Modal Source Architecture & Master Pipeline

## Strategy
Orchestrate a parallel, multi-agent verification sweep across three distinct milestones:

### Milestone 1: Proposal Architecture Audit (R1)
- Target: `docs/graphify_sources_proposal_architecture.md`
- Objectives: Verify metadata (`doc_id: okf-graphify-sources-proposal`, `status: draft`, `version: 1.1.0`) and confirmation of all 6 input categories:
  1. Code Repositories (`repos/`)
  2. Markdown & Text Docs (`docs/`, `repos/`)
  3. PDF Papers & Books (`.pdf` in `raw/` or `graphify add <url>`)
  4. Video & Audio (`.mp4`, `.mp3` via Whisper transcription in `raw/`)
  5. Scraped Web URLs (`graphify add <url>` into `raw/`)
  6. Images & Diagrams (`.png`, `.jpg`, `.svg`)
- Subagents: Explorer (`teamwork_preview_explorer`), Reviewer (`teamwork_preview_reviewer`)

### Milestone 2: Master Pipeline Skill Ingestion Audit (R2)
- Target: `.agents/skills/graphify_pipeline/SKILL.md`
- Objectives: Verify explicit ingestion steps for `.pdf`, `.mp4`/`.mp3`, web URLs, and git repos.
- Subagents: Explorer (`teamwork_preview_explorer`), Reviewer (`teamwork_preview_reviewer`)

### Milestone 3: Test Suite & Forensic Environment Verification (R3)
- Targets: `tests/test_okf.py`, `tests/test_skill_deduplication.py`, full pytest suite, `ALLOW_MAIN_COMMIT=1 uv run agy-verify`
- Objectives:
  1. 100% test pass across unit tests (`test_okf.py` 5/5, `test_skill_deduplication.py` 3/3, full pytest 124/124).
  2. Verify `ALLOW_MAIN_COMMIT=1 uv run agy-verify` returns `decision: allow`.
  3. Perform forensic integrity audit on test outputs, logs, environment state, and scripts.
- Subagents: Worker (`teamwork_preview_worker`), Challenger (`teamwork_preview_challenger`), Forensic Auditor (`teamwork_preview_auditor`)

## Synthesis & Final Reporting
- Aggregate verdicts into `GATE_STATUS.md` and `progress.md`.
- Report findings back to parent sentinel.
