"""Unit tests verifying datamodel-code-generator generated Pydantic V2 models."""

from agy_graphify.models.graph_schema import Edge, GraphData, Node
from agy_graphify.models.orchestration_schema import Agent


def test_generated_models():
    node = Node(id="1", label="Test Node", type="concept")
    edge = Edge(source="1", target="2", type="LINK", weight=0.5)

    graph_data = GraphData(nodes=[node], edges=[edge], metadata={"version": "1.0"})

    json_str = graph_data.model_dump_json()
    assert "Test Node" in json_str
    assert "LINK" in json_str


def test_agent_subtasks_default():
    agent = Agent(role="developer", status="active")
    assert agent.subtasks == []
    # Verify iteration works without TypeError
    task_count = sum(1 for _ in (agent.subtasks or []))
    assert task_count == 0
