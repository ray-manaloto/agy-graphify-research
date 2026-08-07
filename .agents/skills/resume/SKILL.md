---
name: resume
description: Zero-context quick resume for active project goals via StateGraphEngine multi-agent DAG execution.
---

# Resume Active Goal via StateGraphEngine (Zero-Click Auto Execution)

1. **Rehydrate DAG State**:
   - Inspect `.gemini/graph_state.json` via `uv run agy-graph-engine --resume` or `uv run agy-task dag-resume`.
   - Read Level 1 progressive handoff context and uncompleted DAG nodes.

2. **Execute Active DAG Nodes**:
   - Automatically execute the next pending or failed DAG node through the multi-agent engine.
   - Do NOT bypass `StateGraphEngine` DAG node verification.

3. **Verify Final State**:
   - Run `uv run agy-verify` upon completing the resumed DAG workflow.
