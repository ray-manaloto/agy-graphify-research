# Execution Plan: OpenAI Symphony Colibri MoE Benchmarking Campaign

## Goal
Parse and execute the 5-node OpenAI Symphony Colibri MoE Benchmarking Campaign workflow (`docs/workflows/colibri_moe_benchmark.yaml`) via `StateGraphEngine` with `EventDispatcher` emissions, record causal events via `MemoryStoreAdapter` in `.gemini/telemetry/causal_events.jsonl`, achieve 100% test pass rate (70/70 tests), and produce/update `docs/colibri_benchmark_report.md` with throughput, TTFT latency, OTEL spans, and Mermaid streaming pipeline diagrams adhering strictly to OKF spec.

## Milestones

### Milestone 1: Exploration & System State Inspection
- [ ] Dispatch 3 Explorers (`teamwork_preview_explorer`) to inspect:
  - `docs/workflows/colibri_moe_benchmark.yaml`
  - `src/agy_graphify/graph_engine.py`, `src/agy_graphify/telemetry.py`, `src/agy_graphify/workflow_parser.py`
  - Existing tests in `tests/` and CLI/runner tasks in `src/agy_graphify/`
  - Current state of `docs/colibri_benchmark_report.md` and `.gemini/telemetry/causal_events.jsonl`

### Milestone 2: Workflow Execution, Telemetry Recording & Verification
- [ ] Dispatch Worker (`teamwork_preview_worker`) to execute/wire the 5 DAG nodes (`plan_benchmark`, `inspect_metal_shaders`, `execute_benchmark_suite`, `verify_telemetry_spans`, `qa_adversarial_review`) using `StateGraphEngine`, `EventDispatcher`, and `MemoryStoreAdapter`.
- [ ] Run `.venv/bin/python -m pytest` via worker and verify 100% pass rate (70/70 tests).
- [ ] Dispatch Reviewers (`teamwork_preview_reviewer`) and Challengers (`teamwork_preview_challenger`) to audit correctness.
- [ ] Dispatch Forensic Auditor (`teamwork_preview_auditor`) to verify zero integrity violations.

### Milestone 3: OKF Report Update & Final Victory Verification
- [ ] Dispatch Worker (`teamwork_preview_worker`) to update `docs/colibri_benchmark_report.md` with throughput, TTFT latency, OTEL span trace summary, and Mermaid streaming pipeline diagrams (100% OKF compliant).
- [ ] Run `uv run python3 -m agy_graphify.okf docs` or relevant verification task to validate OKF compliance.
- [ ] Perform final Reviewer & Forensic Audit gate checks.
- [ ] Notify Sentinel / parent for final Victory Audit confirmation.
