---
name: graphify-pipeline
description: Master orchestrator skill calling repo-ingest and colibri-benchmark skills for multi-repo extraction and grading.
---

# Graphify Master Pipeline Orchestrator

1. **Ingest & Deduplicate Repositories**:
   - Invoke skill `repo-ingest` to fetch, deduplicate, and clone source repositories into `repos/`.
   - Command: `uv run agy-task ingest-sources`

2. **Execute Colibri Multi-Model Extraction**:
   - Invoke skill `colibri-benchmark` to run deep extraction across Colibri v1.5.0 models (`glm-5.2`, `inkling`, `kimi-k3`, `deepseek-v4-flash`, `olmoe-7b`).
   - Command: `uv run agy-task extract-colibri --model <model_name>`

3. **Grade Models via `/dag`**:
   - Run `/dag` multi-agent review to score and rank model graph outputs:
   - Command: `uv run agy-graph-engine --plan "Grade multi-model graph outputs"`

4. **Multi-Format Fallback & 100% Coverage Verification**:
   - Run `uv run agy-task update-all-sources` to execute `audit_graph_coverage()`.
   - Ensure all non-code repositories (`.md`, `.json`, `.yaml`, `.sh`) receive fallback AST/structural nodes in `graphify-out/graph.json`.
   - Assert `missing_repos_count == 0` before finalizing the extraction pipeline.

