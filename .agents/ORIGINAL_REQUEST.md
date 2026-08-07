# Original User Request

## 2026-07-31T19:44:27Z

Execute multi-agent research, 3rd-party tool evaluation, OpenAI Symphony gap analysis, BuilderIO skills porting, agent memory store integration (cxdb, pensyve), visual diagram enforcement, and framework architectural convergence for agy-graphify-research.

Working directory: /Users/rmanaloto/agy-graphify-research
Integrity mode: development

## Requirements

### R1. 3rd-Party Code Graph & Symbol Navigation Research
Conduct in-depth research and gap analysis across code graph and symbol navigation tools: graphifyy (including native Obsidian vault export & Tree-Sitter AST graphs), cosmtrek/mindwalk, DeusData/codebase-memory-mcp, tirth8205/code-review-graph.

### R2. Agent Memory Stores & Event Stream Persistence (cxdb & pensyve)
- Perform an exhaustive research and gap analysis of agent memory stores: strongdm/cxdb (causal execution database) and major7apps/pensyve (long-term agent memory).
- Generate a dedicated research document docs/agent_memory_tools_research.md (100% OKF compliant).
- Integrate a MemoryStoreAdapter in src/agy_graphify/telemetry.py for persistent, causal agent event streams across subagent sessions.

### R3. BuilderIO Skills Porting & Inventory
- Clone and audit ALL skills from BuilderIO/skills (https://github.com/BuilderIO/skills).
- Port skills strictly at project scope (.gemini/skills/ and .agents/skills/) without modifying global ~/.codex or ~/.gemini.
- Focus on visual skills (UI/flow generation, visual plan presentation).
- Generate comprehensive research report docs/builderio_skills_inventory.md documenting every single skill analyzed so nothing is skipped.

### R4. OpenAI Symphony Gap Analysis & Full Convergence Spec
Perform a detailed gap analysis comparing agy-graphify-research vs OpenAI Symphony (SPEC.md). Port Symphony's declarative YAML workflow spec and event dispatcher into StateGraphEngine while retaining SkillOptAdapter prompt mutation and IntegrityAuditor AST inspection.

### R5. Automated Dependency Cloning, Graphify Persistence & Visual Diagrams
- Implement automated cloning of 3rd-party dependency repositories into vendor/ and index them using graphifyy Tree-Sitter AST graphs and LSP symbols.
- Store all research findings, web searches, and /last30days reports in graphifyy and docs/wiki/ (Obsidian format).
- Enforce visual diagrams (Mermaid architecture diagrams & sequence flows) across all plans, code explanations, and OKF documentation to ensure visual documentation is always 100% in sync with code.

## Acceptance Criteria

### Automated Verification Criteria
- [ ] Research & Gap Analysis report docs/symphony_and_tools_gap_analysis.md created with 100% OKF spec compliance (uv run python3 -m agy_graphify.okf docs)
- [ ] Agent Memory Stores report docs/agent_memory_tools_research.md created covering strongdm/cxdb and major7apps/pensyve
- [ ] BuilderIO skills inventory document docs/builderio_skills_inventory.md created covering 100% of skills from BuilderIO/skills
- [ ] All BuilderIO visual skills ported strictly to project scope (.gemini/skills/ & .agents/skills/)
- [ ] MemoryStoreAdapter integrated into src/agy_graphify/telemetry.py
- [ ] OpenAI Symphony YAML workflow parser and event dispatcher integrated into src/agy_graphify/graph_engine.py
- [ ] Dependency cloning & graphifyy AST indexing wrapper implemented in src/agy_graphify/tasks.py
- [ ] Visual diagrams (Mermaid flowcharts) embedded in docs/ and walkthroughs
- [ ] .venv/bin/python -m pytest passes 100% of unit tests (40+ tests)
- [ ] uv run --active --no-sync agy-verify confirms zero .sh shell scripts and clean AST forensic audit
- [ ] Independent Victory Auditor issues verdict of VICTORY CONFIRMED

## 2026-08-01T00:03:39Z

Execute the OpenAI Symphony Colibri MoE Benchmarking Campaign workflow defined in docs/workflows/colibri_moe_benchmark.yaml using the StateGraphEngine with EventDispatcher and MemoryStoreAdapter.

Working directory: /Users/rmanaloto/agy-graphify-research
Workflow spec: docs/workflows/colibri_moe_benchmark.yaml

## Tasks
1. Parse docs/workflows/colibri_moe_benchmark.yaml using SymphonyWorkflowParser.
2. Execute the 5 DAG nodes (plan_benchmark, inspect_metal_shaders, execute_benchmark_suite, verify_telemetry_spans, qa_adversarial_review) using StateGraphEngine with EventDispatcher emissions.
3. Record causal events in .gemini/telemetry/causal_events.jsonl via MemoryStoreAdapter.
4. Run .venv/bin/python -m pytest to verify 100% test pass rate.
5. Update docs/colibri_benchmark_report.md with final throughput, TTFT latency, OTEL span trace summary, and Mermaid streaming pipeline diagrams.

## Acceptance Criteria
- [ ] 5-node Symphony DAG workflow executed with status 'completed'
- [ ] Causal events recorded in .gemini/telemetry/causal_events.jsonl with SHA-256 hash chains
- [ ] .venv/bin/python -m pytest passes 100% of tests (70/70 tests)
- [ ] docs/colibri_benchmark_report.md updated with 100% OKF spec compliance
- [ ] Independent Victory Auditor verdict of VICTORY CONFIRMED

## 2026-08-07T12:00:32Z

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

