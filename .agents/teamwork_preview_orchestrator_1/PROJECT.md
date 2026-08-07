# Project: agy-graphify-research

## Architecture
agy-graphify-research is an advanced Python graph-orchestration, agent memory, and skill-opt ecosystem.

Key modules:
- `src/agy_graphify/graph_engine.py`: Core `StateGraphEngine` handling workflow state, event dispatch, node execution.
- `src/agy_graphify/telemetry.py`: Telemetry, event streaming, `MemoryStoreAdapter` for causal agent execution memory.
- `src/agy_graphify/tasks.py`: Task definitions, dependency cloning into `vendor/`, graphifyy AST/LSP symbol indexing.
- `src/agy_graphify/okf.py`: Open Knowledge Format (OKF) validator and parser for documentation.
- `src/agy_graphify/verify.py`: Environment and forensic audit verifier.
- `docs/`: OKF-compliant documentation, gap analyses, research reports, and `docs/wiki/` (Obsidian format).
- `.gemini/skills/` and `.agents/skills/`: Ported visual skills.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: 3rd-Party Code Graph Research | Research graphifyy, cosmtrek/mindwalk, DeusData/codebase-memory-mcp, tirth8205/code-review-graph | None | PLANNED |
| 2 | M2: Agent Memory Stores & Telemetry | Research strongdm/cxdb, major7apps/pensyve -> docs/agent_memory_tools_research.md; implement MemoryStoreAdapter in telemetry.py | None | DONE |
| 3 | M3: BuilderIO Skills Porting & Inventory | Clone & audit https://github.com/BuilderIO/skills -> docs/builderio_skills_inventory.md; port visual skills to .gemini/skills & .agents/skills | None | DONE |
| 4 | M4: OpenAI Symphony Gap Analysis & Spec Convergence | Gap analysis -> docs/symphony_and_tools_gap_analysis.md; port Symphony YAML spec & dispatcher into StateGraphEngine in graph_engine.py | M1, M2 | DONE |
| 5 | M5: Dependency Cloning, Graphify Persistence & Diagrams | Implement vendor/ cloning & graphifyy AST indexing in tasks.py; store docs/wiki/; enforce Mermaid flowcharts across docs | M1, M3, M4 | DONE |
| 6 | M6: Automated Verification & Forensic Audit | Run pytest (40+ tests), OKF check, agy-verify, zero .sh check, forensic audit | M1-M5 | DONE |

## Code Layout
- Code root: `src/agy_graphify/`
- Tests: `tests/`
- Documentation: `docs/`
- Skills: `.gemini/skills/`, `.agents/skills/`
- Vendor dependencies: `vendor/`
