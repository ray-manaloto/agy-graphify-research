# Original User Request

## 2026-07-31T19:44:58Z

You are the Project Orchestrator for agy-graphify-research.

Your working directory is: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_orchestrator_1
Project root: /Users/rmanaloto/agy-graphify-research

Refer to the verbatim requirements in /Users/rmanaloto/agy-graphify-research/.agents/ORIGINAL_REQUEST.md.

Your objective is to coordinate and execute all project milestones to satisfy all user requirements and acceptance criteria:

1. R1: 3rd-Party Code Graph & Symbol Navigation Research (graphifyy, cosmtrek/mindwalk, DeusData/codebase-memory-mcp, tirth8205/code-review-graph).
2. R2: Agent Memory Stores & Event Stream Persistence (strongdm/cxdb, major7apps/pensyve). Generate docs/agent_memory_tools_research.md (100% OKF compliant). Integrate MemoryStoreAdapter in src/agy_graphify/telemetry.py.
3. R3: BuilderIO Skills Porting & Inventory. Clone & audit ALL skills from https://github.com/BuilderIO/skills. Port visual skills strictly to project scope (.gemini/skills/ and .agents/skills/). Generate docs/builderio_skills_inventory.md covering 100% of skills.
4. R4: OpenAI Symphony Gap Analysis & Full Convergence Spec. Generate docs/symphony_and_tools_gap_analysis.md (100% OKF spec compliant). Port Symphony's declarative YAML workflow spec and event dispatcher into StateGraphEngine in src/agy_graphify/graph_engine.py while retaining SkillOptAdapter prompt mutation and IntegrityAuditor AST inspection.
5. R5: Automated Dependency Cloning, Graphify Persistence & Visual Diagrams. Implement automated cloning into vendor/ and index using graphifyy Tree-Sitter AST graphs and LSP symbols in src/agy_graphify/tasks.py. Store findings in graphifyy and docs/wiki/ (Obsidian format). Enforce Mermaid flowcharts across docs/ and walkthroughs.
6. Automated Verification:
   - `uv run python3 -m agy_graphify.okf docs` (OKF compliance)
   - `.venv/bin/python -m pytest` (passes 100% of tests, 40+ tests)
   - `uv run --active --no-sync agy-verify` (zero .sh scripts, clean AST forensic audit)

Maintain your plan, progress.md, and status in your working directory. Keep your progress.md updated after every subtask. When all work and verification are complete, notify the Sentinel.
