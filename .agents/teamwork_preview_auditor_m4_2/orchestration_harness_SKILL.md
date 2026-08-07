---
name: orchestration-harness
description: Multi-agent graph orchestration harness and validation skill plugin wrapping modular mise tasks and agy_graphify library functions.
---

# Multi-Agent Orchestration Graph Harness & Validation Skill

This skill provides an automated, modular wrapper to dispatch multi-agent graph workflows, collect telemetry logs, verify OKF documentation, and run harness validation checks across subagent roles (`coordinator`, `researcher`, `developer`, `verifier`, `qa_reviewer`, `okf_specialist`, `learning_agent`).

## Usage

### 1. Execute Multi-Agent Harness Validation
Run the modular validation task:
```bash
mise run harness-validate
```

### 2. Dispatch Parameterized Orchestration Workflow
```bash
mise run orchestrate -- "Benchmarking MoE Engine" --stage stage-3 --roles coordinator researcher developer verifier --execution-mode dag
```

### 3. Collect Conversation Telemetry
```bash
mise run telemetry
```
