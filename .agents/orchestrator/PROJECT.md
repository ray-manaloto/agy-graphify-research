# Project: agy-graphify-research — OpenAI Symphony Colibri MoE Benchmarking Campaign

## Architecture
StateGraphEngine with EventDispatcher and MemoryStoreAdapter for declarative YAML workflow execution and causal event telemetry tracking.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & System State Inspection | Inspect docs/workflows/colibri_moe_benchmark.yaml, src/agy_graphify/, tests/, and existing reports | None | DONE |
| 2 | Workflow Execution & Telemetry Verification | Execute 5-node DAG via StateGraphEngine + MemoryStoreAdapter, verify 70/70 pytest suite | M1 | DONE |
| 3 | OKF Report Update & Audit Gating | Update docs/colibri_benchmark_report.md (OKF compliant, Mermaid diagrams), final Forensic Audit | M2 | DONE |

## Interface Contracts
- `SymphonyWorkflowParser.parse_yaml_file(path)` -> `SymphonyWorkflowSpec` / `GraphEngineSchema`
- `StateGraphEngine.execute_graph(schema)` -> execution state & lifecycle events via `EventDispatcher`
- `MemoryStoreAdapter.append_causal_event(event)` -> appends to `.gemini/telemetry/causal_events.jsonl` with SHA-256 hash chains

## Code Layout
- `src/agy_graphify/graph_engine.py`: StateGraphEngine, EventDispatcher, SymphonyWorkflowParser
- `src/agy_graphify/workflow_parser.py`: Entrypoint alias for SymphonyWorkflowParser
- `src/agy_graphify/telemetry.py`: MemoryStoreAdapter, causal event tracking, SHA-256 hash chains
- `docs/workflows/colibri_moe_benchmark.yaml`: Symphony workflow spec file
- `docs/colibri_benchmark_report.md`: Open Knowledge Format benchmarking report
- `scripts/execute_colibri_benchmark.py`: Execution script for 5-node Symphony DAG workflow
- `tests/test_colibri_moe_benchmark.py`: Integration tests for benchmarking campaign
- `tests/`: Unit tests (Pytest)
