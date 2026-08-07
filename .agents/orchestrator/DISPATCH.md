## 2026-08-07T12:00:32Z

Consolidate repository source ingestion and Colibri knowledge graph extraction into `graphify_pipeline` (`.agents/skills/graphify_pipeline/SKILL.md`) as the single canonical master skill, eliminating duplicate skills while preserving 100% of source parsing, deduplication, differential tracking, and extraction features, verified repeatably via unit test suite.

Working directory: `/Users/rmanaloto/agy-graphify-research`
Integrity mode: development

Requirements:
- R1. Single Canonical Master Skill (`graphify_pipeline`): Ensure `.agents/skills/graphify_pipeline/SKILL.md` is the single master skill containing complete source parsing (GitHub URLs, Crates.io packages), deduplication against `config/sources.json`, Git SHA differential tracking (`uv run agy-task update-all-sources`), and local zero-token Colibri graph extraction (`uv run agy-task colibri-graphify`).
- R2. Zero Duplicate Symlinks or Broken Skills: Verify `.agents/skills/` contains zero duplicate or broken symlinks (`visual-edit`, `visual-plan`, `visual-recap`), retaining only clean canonical underscore directories.
- R3. Feature Retention & Skill Deduplication Test Suite: Verify `tests/test_skill_deduplication.py` includes repeatable unit test assertions for:
  * Zero duplicate or broken symlink files.
  * Valid YAML frontmatter headers across all skill `SKILL.md` files.
  * Feature keyword presence (`update-all-sources`, `colibri-graphify`, `Deduplicate`, `graphify-out/graph.json`, `GRAPH_REPORT.md`) in `graphify_pipeline/SKILL.md`.

Acceptance Criteria:
- `.agents/skills/` contains zero duplicate or broken symlinks.
- `graphify_pipeline` serves as the single master skill retaining 100% of ingestion and extraction features.
- 124/124 unit tests pass (`uv run pytest`).
- `ALLOW_MAIN_COMMIT=1 uv run agy-verify` returns `decision: allow`.
