# Project Plan: Teamwork Framework Gap Analysis

## Architecture & Goal
Analyze and compare the `/teamwork-preview` framework against `agy-graphify-research` multi-agent orchestration framework, generating a comprehensive, OKF-compliant research document in `docs/teamwork_framework_gap_analysis.md`.

## Architectural Comparison Dimensions
1. **Agent Subsystem Archetypes & Roles**: Sentinel / Orchestrator / Victory Auditor vs Coordinator / Researcher / Developer / Verifier / QA / OKF / Learning Agent
2. **Workflow & Graph Execution**: DAG nodes vs Sentinel-Orchestrator-Explorer multi-level delegation
3. **Audit & Verification Mechanisms**: Mandatory 3-phase Victory Audit / Cheating Detection vs Unit Tests / OKF validator / EnvironmentVerifier
4. **Self-Learning & Telemetry**: SkillOpt prompt mutation / Phoenix OTEL vs Sentinel crons / briefing handoffs
5. **State Persistence & Checkpointing**: JSON graph state / atomic writes vs Sentinel briefing / handoff files

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Technical Exploration | Explore `agy-graphify-research` codebase (`src/agy_graphify/`, `schemas/`, `docs/`, `AGENTS.md`) and `/teamwork-preview` specs to collect precise feature comparison data | None | DONE |
| 2 | Report Generation | Draft `docs/teamwork_framework_gap_analysis.md` with complete YAML frontmatter (title, doc_id: okf-teamwork-gap-001, version: 1.0.0, type: report, status: approved) and required sections | M1 | DONE (Remediation Iteration 2) |
| 3 | Review, Challenge & Audit | Review correctness, perform empirical OKF validation, and conduct Forensic Integrity Audit | M2 | DONE (CLEAN Audit Verdict) |
