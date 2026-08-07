# OpenAI Symphony Colibri MoE Benchmark Workflow & Parser Analysis

## Executive Summary
This report presents a line-by-line analysis of `docs/workflows/colibri_moe_benchmark.yaml` and an architectural evaluation of `SymphonyWorkflowParser` and its associated schemas (`SymphonyWorkflowSpec`, `SymphonyNodeSpec`, `GraphEngineSchema`, `Node`). 

The 5-node workflow defines a linear DAG benchmarking campaign for the Colibri MoE engine. Parsing `colibri_moe_benchmark.yaml` with `SymphonyWorkflowParser` operates successfully and produces a valid `GraphEngineSchema` with 5 pending task nodes that pass Kahn's topological sort without cycles. 

However, two structural gaps were identified:
1. **Module Location**: `src/agy_graphify/workflow_parser.py` does not exist as a standalone file; `SymphonyWorkflowParser` is currently implemented inside `src/agy_graphify/graph_engine.py`.
2. **Schema Field Truncation**: Attributes defined in `SymphonyNodeSpec` (`inputs`, `outputs`, `retry_policy`) and `SymphonyWorkflowSpec` (`context`) are not mapped into `Node` or `GraphEngineSchema` during `to_graph_schema()` transformation.

---

## 1. Line-by-Line Analysis of `docs/workflows/colibri_moe_benchmark.yaml`

### File Metadata (Lines 1–6)
```yaml
1: # OpenAI Symphony Declarative Workflow Spec for Colibri MoE Benchmarking Campaign
2: name: colibri_moe_benchmark_workflow
3: version: 1.0.0
4: description: Autonomous multi-agent benchmarking campaign for Colibri MoE engine (Apple Silicon M2 Max Metal Compute & Direct I/O).
5: execution_mode: dag
6: max_remediations: 3
```
- **Line 2 (`name`)**: Identifies the workflow as `colibri_moe_benchmark_workflow`. Mapped to `GraphEngineSchema.graph_id`.
- **Line 3 (`version`)**: `1.0.0`. Validated by `SymphonyWorkflowSpec`.
- **Line 4 (`description`)**: Describes campaign scope (Apple Silicon M2 Max Metal Compute & Direct I/O).
- **Line 5 (`execution_mode`)**: `dag`. Enum match with `ExecutionMode.dag`.
- **Line 6 (`max_remediations`)**: Set to `3`. Limits remediation loops before failing workflow.

---

### Node Breakdown (Lines 8–40)

#### Node 1: `plan_benchmark` (Lines 9–12)
```yaml
9:   - id: plan_benchmark
10:     node_type: task
11:     role: coordinator
12:     instructions: Define benchmarking parameters, tensor cache configurations, and hardware monitoring profiles for Colibri MoE.
```
- **ID**: `plan_benchmark`
- **Node Type**: `task` (`NodeType.task`)
- **Role**: `coordinator`
- **Instructions**: Parameters definition, tensor cache configs, hardware monitoring setup.
- **Dependencies**: None (root DAG node).
- **Inputs/Outputs/Commands**: Implicit / default.

#### Node 2: `inspect_metal_shaders` (Lines 14–19)
```yaml
14:   - id: inspect_metal_shaders
15:     node_type: task
16:     role: researcher
17:     instructions: Inspect Metal compute shaders and OpenMP Direct I/O block streaming in scratch/colibri/repo/c/ using Tree-Sitter AST graphs.
18:     dependencies:
19:       - plan_benchmark
```
- **ID**: `inspect_metal_shaders`
- **Node Type**: `task` (`NodeType.task`)
- **Role**: `researcher`
- **Instructions**: Inspect Metal shaders & OpenMP Direct I/O in `scratch/colibri/repo/c/` via Tree-Sitter AST graphs.
- **Dependencies**: `['plan_benchmark']`. Executes after Node 1.

#### Node 3: `execute_benchmark_suite` (Lines 21–26)
```yaml
21:   - id: execute_benchmark_suite
22:     node_type: task
23:     role: developer
24:     instructions: Execute token generation throughput and TTFT latency benchmark matrix under varying expert cache allocations.
25:     dependencies:
26:       - inspect_metal_shaders
```
- **ID**: `execute_benchmark_suite`
- **Node Type**: `task` (`NodeType.task`)
- **Role**: `developer`
- **Instructions**: Run throughput & TTFT latency matrix under varying expert cache allocations.
- **Dependencies**: `['inspect_metal_shaders']`. Executes after Node 2.

#### Node 4: `verify_telemetry_spans` (Lines 28–33)
```yaml
28:   - id: verify_telemetry_spans
29:     node_type: task
30:     role: verifier
31:     instructions: Audit OTEL spans in Arize Phoenix and verify causal DAG hash chain integrity in .gemini/telemetry/causal_events.jsonl.
32:     dependencies:
33:       - execute_benchmark_suite
```
- **ID**: `verify_telemetry_spans`
- **Node Type**: `task` (`NodeType.task`)
- **Role**: `verifier`
- **Instructions**: Audit OTEL spans in Phoenix and verify causal DAG hash chain integrity in `.gemini/telemetry/causal_events.jsonl`.
- **Dependencies**: `['execute_benchmark_suite']`. Executes after Node 3.

#### Node 5: `qa_adversarial_review` (Lines 35–40)
```yaml
35:   - id: qa_adversarial_review
36:     node_type: task
37:     role: qa_reviewer
38:     instructions: Conduct adversarial stress test review under memory pressure and issue victory audit verdict.
39:     dependencies:
40:       - verify_telemetry_spans
```
- **ID**: `qa_adversarial_review`
- **Node Type**: `task` (`NodeType.task`)
- **Role**: `qa_reviewer`
- **Instructions**: Adversarial memory pressure review & victory audit verdict.
- **Dependencies**: `['verify_telemetry_spans']`. Executes after Node 4.

---

### DAG Topology & Dependency Matrix

| Node ID | Node Type | Assigned Role | Immediate Dependencies | Topological Order Index |
| :--- | :--- | :--- | :--- | :--- |
| `plan_benchmark` | `task` | `coordinator` | None | 0 |
| `inspect_metal_shaders` | `task` | `researcher` | `plan_benchmark` | 1 |
| `execute_benchmark_suite` | `task` | `developer` | `inspect_metal_shaders` | 2 |
| `verify_telemetry_spans` | `task` | `verifier` | `execute_benchmark_suite` | 3 |
| `qa_adversarial_review` | `task` | `qa_reviewer` | `verify_telemetry_spans` | 4 |

**Execution Flow**:
`plan_benchmark` ➔ `inspect_metal_shaders` ➔ `execute_benchmark_suite` ➔ `verify_telemetry_spans` ➔ `qa_adversarial_review`

---

## 2. Parser & Schema Alignment Analysis

### Location of `SymphonyWorkflowParser`
- **Requested Path**: `src/agy_graphify/workflow_parser.py`
- **Actual Location**: Defined in `src/agy_graphify/graph_engine.py` (lines 63–99).
- **Supporting Models**: Defined in `src/agy_graphify/models/graph_engine_schema.py`.
- **Status**: `src/agy_graphify/workflow_parser.py` does not currently exist. Attempts to import `from agy_graphify.workflow_parser import SymphonyWorkflowParser` will fail with `ModuleNotFoundError`.

### Parser Parsing Pipeline & Model Mapping
```
colibri_moe_benchmark.yaml (YAML String / File)
       │
       ▼ safe_load()
Raw Dictionary
       │
       ▼ SymphonyWorkflowSpec.model_validate()
SymphonyWorkflowSpec Pydantic Object
       │
       ▼ SymphonyWorkflowParser.to_graph_schema()
GraphEngineSchema (containing Node objects)
```

### Transformation Field Mapping Summary

| Field in YAML Spec | `SymphonyWorkflowSpec` / `SymphonyNodeSpec` | `GraphEngineSchema` / `Node` | Status |
| :--- | :--- | :--- | :--- |
| `name` | `spec.name` | `schema.graph_id` | ✅ Mapped |
| `execution_mode` | `spec.execution_mode` | `schema.execution_mode` | ✅ Mapped |
| `max_remediations` | `spec.max_remediations` | `schema.max_remediations` | ✅ Mapped |
| `context` | `spec.context` | N/A | ⚠️ Dropped in `to_graph_schema()` |
| `node.id` | `n_spec.id` | `node.id` | ✅ Mapped |
| `node.node_type` | `n_spec.node_type` | `node.node_type` | ✅ Mapped |
| `node.role` | `n_spec.role` | `node.subagent_role` | ✅ Mapped |
| `node.instructions` | `n_spec.instructions` | `node.task_action` | ✅ Mapped |
| `node.dependencies` | `n_spec.dependencies` | `node.dependencies` | ✅ Mapped |
| `node.inputs` | `n_spec.inputs` | N/A | ⚠️ Dropped in `Node` schema |
| `node.outputs` | `n_spec.outputs` | N/A | ⚠️ Dropped in `Node` schema |
| `node.retry_policy` | `n_spec.retry_policy` | N/A | ⚠️ Dropped in `Node` schema |

---

## 3. Verification & Execution Results

1. **YAML Parser Verification**: Executed `SymphonyWorkflowParser.parse_yaml_file(Path("docs/workflows/colibri_moe_benchmark.yaml"))` using `.venv/bin/python`. The spec parses into a 5-node `GraphEngineSchema` without errors.
2. **DAG Validation**: `StateGraphEngine.validate_dag()` confirmed topological order:
   `['plan_benchmark', 'inspect_metal_shaders', 'execute_benchmark_suite', 'verify_telemetry_spans', 'qa_adversarial_review']` with zero static cycle errors.
3. **Unit Tests**: Ran `.venv/bin/pytest tests/test_graph_engine.py`. All 10 tests passed (100%).

---

## 4. Recommendations for Implementation & Alignment

1. **Module File Creation/Alias**: Create `src/agy_graphify/workflow_parser.py` that re-exports `SymphonyWorkflowParser` from `agy_graphify.graph_engine` or extracts the parser class, ensuring compatibility with imports targeting `agy_graphify.workflow_parser`.
2. **Schema Enrichment**: Update `Node` in `src/agy_graphify/models/graph_engine_schema.py` to optionally preserve `inputs`, `outputs`, and `retry_policy` if node payload metadata is needed during subagent execution.
