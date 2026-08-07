import asyncio
import json
import yaml
from pathlib import Path
from pydantic import ValidationError

from agy_graphify.workflow_parser import SymphonyWorkflowParser
from agy_graphify.graph_engine import StateGraphEngine, DAGCycleError, MaxRemediationExceededError
from agy_graphify.models.graph_engine_schema import GraphEngineSchema, Node, NodeType, Status, Status1, ExecutionMode

def run_edge_case_tests():
    results = []

    # -------------------------------------------------------------
    # Category 1: Invalid YAML Parsing
    # -------------------------------------------------------------
    
    # Case 1.1: Syntactically invalid YAML
    bad_yaml_syntax = """
    name: bad_yaml
    nodes:
      - id: node1
        node_type: task
        dependencies: [unclosed_list
    """
    try:
        SymphonyWorkflowParser.parse_yaml_str(bad_yaml_syntax)
        results.append({"case": "Invalid YAML Syntax", "status": "FAIL", "reason": "Expected error but passed"})
    except yaml.YAMLError as exc:
        results.append({"case": "Invalid YAML Syntax", "status": "PASS", "caught": f"yaml.YAMLError: {exc}"})
    except Exception as exc:
        results.append({"case": "Invalid YAML Syntax", "status": "PASS", "caught": f"{type(exc).__name__}: {exc}"})

    # Case 1.2: Invalid Schema (missing required fields, e.g. name or nodes)
    bad_yaml_schema = """
    invalid_root_key: foo
    nodes:
      - invalid_node_field: bar
    """
    try:
        SymphonyWorkflowParser.parse_yaml_str(bad_yaml_schema)
        results.append({"case": "Invalid YAML Schema", "status": "FAIL", "reason": "Expected ValidationError but passed"})
    except ValidationError as exc:
        results.append({"case": "Invalid YAML Schema", "status": "PASS", "caught": f"ValidationError: {len(exc.errors())} validation errors"})
    except Exception as exc:
        results.append({"case": "Invalid YAML Schema", "status": "PASS", "caught": f"{type(exc).__name__}: {exc}"})

    # Case 1.3: Node with missing required fields (e.g. missing node_type or id)
    bad_yaml_node_missing = """
    name: missing_node_id
    nodes:
      - role: tester
    """
    try:
        SymphonyWorkflowParser.parse_yaml_str(bad_yaml_node_missing)
        results.append({"case": "YAML Node Missing Required Fields", "status": "FAIL", "reason": "Expected ValidationError but passed"})
    except ValidationError as exc:
        results.append({"case": "YAML Node Missing Required Fields", "status": "PASS", "caught": f"ValidationError: {len(exc.errors())} validation errors"})
    except Exception as exc:
        results.append({"case": "YAML Node Missing Required Fields", "status": "PASS", "caught": f"{type(exc).__name__}: {exc}"})

    # -------------------------------------------------------------
    # Category 2: Cyclic Dependencies in DAG
    # -------------------------------------------------------------

    engine = StateGraphEngine()

    # Case 2.1: Direct 2-node cycle (A -> B -> A)
    node_a = Node(id="node_a", node_type=NodeType.task, status=Status1.pending, dependencies=["node_b"])
    node_b = Node(id="node_b", node_type=NodeType.task, status=Status1.pending, dependencies=["node_a"])
    try:
        engine.validate_dag([node_a, node_b])
        results.append({"case": "Direct 2-Node Cycle (A <-> B)", "status": "FAIL", "reason": "Expected DAGCycleError but passed"})
    except DAGCycleError as exc:
        results.append({"case": "Direct 2-Node Cycle (A <-> B)", "status": "PASS", "caught": f"DAGCycleError: {exc}"})
    except Exception as exc:
        results.append({"case": "Direct 2-Node Cycle (A <-> B)", "status": "FAIL", "reason": f"Unexpected exception: {exc}"})

    # Case 2.2: Indirect 3-node cycle (A -> B -> C -> A)
    n1 = Node(id="n1", node_type=NodeType.task, status=Status1.pending, dependencies=["n3"])
    n2 = Node(id="n2", node_type=NodeType.task, status=Status1.pending, dependencies=["n1"])
    n3 = Node(id="n3", node_type=NodeType.task, status=Status1.pending, dependencies=["n2"])
    try:
        engine.validate_dag([n1, n2, n3])
        results.append({"case": "Indirect 3-Node Cycle (A -> B -> C -> A)", "status": "FAIL", "reason": "Expected DAGCycleError but passed"})
    except DAGCycleError as exc:
        results.append({"case": "Indirect 3-Node Cycle (A -> B -> C -> A)", "status": "PASS", "caught": f"DAGCycleError: {exc}"})
    except Exception as exc:
        results.append({"case": "Indirect 3-Node Cycle (A -> B -> C -> A)", "status": "FAIL", "reason": f"Unexpected exception: {exc}"})

    # Case 2.3: Self-referencing node (A -> A)
    n_self = Node(id="n_self", node_type=NodeType.task, status=Status1.pending, dependencies=["n_self"])
    try:
        engine.validate_dag([n_self])
        results.append({"case": "Self-Referencing Node (A -> A)", "status": "FAIL", "reason": "Expected DAGCycleError but passed"})
    except DAGCycleError as exc:
        results.append({"case": "Self-Referencing Node (A -> A)", "status": "PASS", "caught": f"DAGCycleError: {exc}"})
    except Exception as exc:
        results.append({"case": "Self-Referencing Node (A -> A)", "status": "FAIL", "reason": f"Unexpected exception: {exc}"})

    # -------------------------------------------------------------
    # Category 3: Missing / Non-existent Dependencies
    # -------------------------------------------------------------

    # Case 3.1: Node depends on non-existent node ID
    n_valid = Node(id="valid_node", node_type=NodeType.task, status=Status1.pending, dependencies=["ghost_node"])
    try:
        engine.validate_dag([n_valid])
        results.append({"case": "Non-existent Dependency ID", "status": "FAIL", "reason": "Expected ValueError but passed"})
    except ValueError as exc:
        results.append({"case": "Non-existent Dependency ID", "status": "PASS", "caught": f"ValueError: {exc}"})
    except Exception as exc:
        results.append({"case": "Non-existent Dependency ID", "status": "FAIL", "reason": f"Unexpected exception: {exc}"})

    # -------------------------------------------------------------
    # Category 4: Execution Engine Boundary Conditions
    # -------------------------------------------------------------

    # Case 4.1: Remediation loop count exceeding max_remediations
    rem_node_1 = Node(id="rem_1", node_type=NodeType.remediation, status=Status1.pending)
    rem_node_2 = Node(id="rem_2", node_type=NodeType.remediation, status=Status1.pending, dependencies=["rem_1"])
    schema_rem = GraphEngineSchema(
        graph_id="excess_remediation_test",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        remediation_count=3,
        max_remediations=3,
        nodes=[rem_node_1, rem_node_2],
    )
    try:
        asyncio.run(engine.execute_graph(schema_rem))
        results.append({"case": "Max Remediation Exceeded", "status": "FAIL", "reason": "Expected MaxRemediationExceededError but passed"})
    except MaxRemediationExceededError as exc:
        results.append({"case": "Max Remediation Exceeded", "status": "PASS", "caught": f"MaxRemediationExceededError: {exc}"})
    except Exception as exc:
        results.append({"case": "Max Remediation Exceeded", "status": "FAIL", "reason": f"Unexpected exception: {exc}"})

    # Case 4.2: Dependency Failure Cascade (node fails -> dependent node skipped)
    n_fail = Node(id="failing_node", node_type=NodeType.task, status=Status1.pending)
    n_dependent = Node(id="dep_node", node_type=NodeType.task, status=Status1.pending, dependencies=["failing_node"])
    
    def failing_handler(node):
        if node.id == "failing_node":
            raise RuntimeError("Simulated failure in handler")

    schema_cascade = GraphEngineSchema(
        graph_id="cascade_failure_test",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        nodes=[n_fail, n_dependent],
    )
    res_schema = asyncio.run(engine.execute_graph(schema_cascade, task_handlers={"failing_node": failing_handler}))
    
    if n_fail.status == Status1.failed and n_dependent.status == Status1.skipped and res_schema.status == Status.failed:
        results.append({
            "case": "Dependency Failure Cascade",
            "status": "PASS",
            "caught": f"failing_node={n_fail.status.value}, dep_node={n_dependent.status.value}, graph={res_schema.status.value}"
        })
    else:
        results.append({
            "case": "Dependency Failure Cascade",
            "status": "FAIL",
            "reason": f"Incorrect statuses: failing_node={n_fail.status}, dep_node={n_dependent.status}"
        })

    # Output Summary
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run_edge_case_tests()
