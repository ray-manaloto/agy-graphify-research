# Comprehensive Technical Analysis: Graph Engine, Telemetry Event Dispatching, and Causal DAG Logging

## 1. Overview & Objective
This report details the architectural investigation of DAG node execution and lifecycle event dispatching in `src/agy_graphify/graph_engine.py`, causal event formatting, SHA-256 hash chaining, and append mechanics in `src/agy_graphify/telemetry.py`, and the status and structure of `.gemini/telemetry/causal_events.jsonl`.

---

## 2. StateGraphEngine & EventDispatcher Analysis (`src/agy_graphify/graph_engine.py`)

### 2.1 `EventDispatcher` Architecture
- **Location**: `src/agy_graphify/graph_engine.py` (lines 38–62).
- **Core Responsibilities**: Serves as an asynchronous event bus for lifecycle observers across the DAG execution lifecycle.
- **Key Attributes**:
  - `_listeners: dict[EventType, list[Callable[[SymphonyEvent], Awaitable[None] | None]]]`: Uses `defaultdict(list)` to store callbacks registered for each `EventType`.
  - `_event_history: list[SymphonyEvent]`: Append-only in-memory log of all dispatched `SymphonyEvent` instances.
- **Methods**:
  - `subscribe(event_type: EventType, listener: Callable)`: Appends subscriber functions to the listener list for `event_type`.
  - `dispatch(event: SymphonyEvent)`:
    1. Appends `event` to `_event_history`.
    2. Logs a debug message with the event type, node ID, and graph ID.
    3. Iterates over registered listeners for `event.event_type`.
    4. Evaluates sync functions or awaits coroutines (`asyncio.iscoroutine(res)`).
    5. **Exception Isolation**: Encloses listener invocation in a `try...except Exception` block, logging errors without interrupting graph execution.

### 2.2 `StateGraphEngine` DAG Execution Flow
- **Location**: `src/agy_graphify/graph_engine.py` (lines 102–389).
- **DAG Validation & Topological Sorting**:
  - `validate_dag(nodes)` implements Kahn's algorithm (indegree calculation + queue traversal).
  - Validates that all node dependencies exist in the node set (raises `ValueError` if missing).
  - Detects static dependency cycles: raises `DAGCycleError` if `len(topo_order) != len(nodes)`.
- **Verification Subgraph Expansion**:
  - `expand_verification_subgraph(nodes)` expands `NodeType.task` nodes into a 4-node verification sequence: `task` → `reviewer` → `challenger` → `auditor`.
- **Atomic State Persistence**:
  - `save_state_atomic(schema)` uses `asyncio.Lock()` and a temporary file (`tempfile.NamedTemporaryFile` + `os.replace`) to atomically update `.gemini/graph_state.json`.
- **Execution Algorithm (`execute_graph`)**:
  1. Computes `topo_order = validate_dag(schema.nodes)`.
  2. Sets `schema.status = Status.running`, saves state atomically, and dispatches `EventType.WORKFLOW_STARTED`.
  3. Iterates sequentially through `node_id` in `topo_order`:
     - **Dependency Check**: Checks dependency statuses. If any parent node has `status == Status1.failed`, marks node `status = Status1.skipped`, sets `error_message = "Skipped due to failed dependency"`, dispatches `EventType.NODE_SKIPPED`, and skips execution.
     - **Node Startup**: Sets `node.status = Status1.running`, saves state, dispatches `EventType.NODE_STARTED`.
     - **Remediation Handling**: If `node.node_type == NodeType.remediation`, increments `remediation_count`. If `remediation_count > max_remediations`, marks node and schema `failed`, saves state, dispatches `EventType.NODE_FAILED` and `EventType.WORKFLOW_FAILED`, and raises `MaxRemediationExceededError`. Otherwise dispatches `EventType.REMEDIATION_TRIGGERED`.
     - **Handler Invocation**: If `task_handlers` contains `node.id`, executes sync handler or awaits async handler.
     - **Node Completion**: Sets `node.status = Status1.passed`, dispatches `EventType.NODE_COMPLETED`.
     - **Error Trapping**: On execution exception (not `MaxRemediationExceededError`), marks `node.status = Status1.failed`, sets `node.error_message`, and dispatches `EventType.NODE_FAILED`.
  4. Final Status Determination: Checks for any failed nodes across the graph. Updates `schema.status` to `Status.failed` or `Status.completed`, saves state, and dispatches `EventType.WORKFLOW_FAILED` or `EventType.WORKFLOW_COMPLETED`.

### 2.3 Event Types & Convergence
- Dispatches `SymphonyEvent` models containing UUID `event_id`, UTC ISO timestamp, `graph_id`, `node_id`, `payload`, and `error_message`.
- Dispatched event lifecycle:
  - `WORKFLOW_STARTED`
  - `NODE_STARTED`
  - `NODE_SKIPPED`
  - `REMEDIATION_TRIGGERED`
  - `NODE_FAILED`
  - `NODE_COMPLETED`
  - `WORKFLOW_COMPLETED`
  - `WORKFLOW_FAILED`

---

## 3. MemoryStoreAdapter & SHA-256 Cryptographic Hash Chaining (`src/agy_graphify/telemetry.py`)

### 3.1 `CausalTelemetryEvent` Model & Hash Formula
- **Location**: `src/agy_graphify/telemetry.py` (lines 29–46).
- **Data Model Attributes**:
  - `event_id`: Unique identifier (formatted as `"{conversation_id}-{step_index}-{idx}"`).
  - `conversation_id`: Active conversation ID.
  - `causal_parent_id`: Parent conversation or task ID.
  - `step_index`: Execution step index.
  - `event_type`: Event category (e.g. `USER_INPUT`, `TOOL_CALL`).
  - `subagent_role`: Optional subagent role.
  - `status`: Execution status (default `"DONE"`).
  - `content_summary`: Truncated summary of event content.
  - `tool_calls`: List of tool invocation dictionaries.
  - `causal_hash`: Cryptographic SHA-256 hash string.
- **SHA-256 Computation**:
  ```python
  def compute_causal_hash(self, prev_hash: str = "") -> str:
      payload = f"{self.event_id}:{self.conversation_id}:{self.causal_parent_id}:{self.step_index}:{self.status}:{prev_hash}"
      return hashlib.sha256(payload.encode("utf-8")).hexdigest()
  ```
  Each event's hash incorporates its metadata alongside `prev_hash` (the `causal_hash` of the immediately preceding event), creating a tamper-evident cryptographic hash chain.

### 3.2 `MemoryStoreAdapter` Operations & File Writing
- **Location**: `src/agy_graphify/telemetry.py` (lines 48–112).
- **Initialization**: Sets `self.causal_events_file = output_dir / "causal_events.jsonl"` and `self._last_hash = ""`.
- **`append_causal_event(event: CausalTelemetryEvent)` Workflow**:
  1. Calculates `event.causal_hash = event.compute_causal_hash(self._last_hash)`.
  2. Updates state: `self._last_hash = event.causal_hash`.
  3. Stores event in `self._causal_dag[event.conversation_id]`.
  4. Ensures directory `.gemini/telemetry/` exists.
  5. Appends `event.model_dump_json() + "\n"` to `causal_events.jsonl` using mode `"a"`.
- **Remediation Rules Integration**:
  - `record_remediation_rules()` extracts failed tool calls, deduplicates them using key `f"{tool}:{json_args}"`, and persists them to `.gemini/telemetry/remediation_rules.json`.

---

## 4. Status & Structure of `.gemini/telemetry/causal_events.jsonl`

### 4.1 Existence Check
- **Verification Result**: `.gemini/telemetry/causal_events.jsonl` currently does **not** exist in `.gemini/telemetry/` because `TelemetryCollector.collect_events()` has not yet been executed in the root workspace directory.
- **Existing Artifacts in `.gemini/telemetry/`**:
  - `events.jsonl` (816 standard telemetry event lines)
  - `events.msgpack` (Binary serialized event storage)
  - `remediation_rules.json` (Self-healing rule store)
  - `phoenix/` (Arize Phoenix OTEL local dashboard traces)

### 4.2 Formatted JSONL Line Schema
Upon invocation of `append_causal_event`, each entry in `causal_events.jsonl` follows this exact JSON structure:
```json
{
  "event_id": "c12faba1-6d55-48ee-bb78-e7b93b5ae38b-0-0",
  "conversation_id": "c12faba1-6d55-48ee-bb78-e7b93b5ae38b",
  "causal_parent_id": "c12faba1-6d55-48ee-bb78-e7b93b5ae38b",
  "step_index": 0,
  "event_type": "USER_INPUT",
  "subagent_role": null,
  "status": "DONE",
  "content_summary": "<USER_REQUEST>...",
  "tool_calls": [],
  "causal_hash": "a8f3b2c1..."
}
```

---

## 5. Verification & Test Execution Results
- Executed unit tests in `tests/test_graph_engine.py` and `tests/test_telemetry.py` via `uv run --no-sync pytest`.
- All 16 unit tests passed successfully (100% pass rate).
