---
name: dag
description: Execute multi-agent state graph workflows (DAG) for complex tasks, natural language prompt ingestion, and goal verification.
---

# Multi-Agent State Graph Engine (DAG Dispatch)

1. **Parse & Plan**:
   - Ingest user goal arguments (`$ARGUMENTS`).
   - Run `uv run agy-graph-engine --plan "$ARGUMENTS"` to generate the `GraphState` DAG nodes in `.gemini/graph_state.json`.

2. **Execute Multi-Agent Subtasks**:
   - For each DAG node in topological order:
     - Invoke dedicated subagents (`research`, `developer`, `verifier`, `qa_reviewer`) according to node roles.
     - Record OpenTelemetry span traces to `.gemini/telemetry/`.
     - Atomically update `.gemini/graph_state.json` upon node completion.

3. **Verify & Audit**:
   - Run `uv run agy-verify` to ensure zero `.sh` shell script violations and clean environment state.
   - Run `PYTHONPATH=src .venv/bin/python3 -m pytest tests/` to confirm 100% test pass.
