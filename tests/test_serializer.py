"""Unit tests for SerializerEngine (msgspec MsgPack & orjson)."""

from agy_graphify.models.graph_schema import Edge, GraphData, Node
from agy_graphify.serializer import SerializerEngine


def test_serializer_msgpack_and_orjson():
    node = Node(id="1", label="Binary Node", type="concept")
    edge = Edge(source="1", target="2", type="BINARY_LINK", weight=0.9)
    graph = GraphData(nodes=[node], edges=[edge], metadata={"format": "binary"})

    # Test MsgPack binary serialization & deserialization
    msgpack_bytes = SerializerEngine.to_msgpack_bytes(graph)
    assert isinstance(msgpack_bytes, bytes)

    deserialized = SerializerEngine.from_msgpack_bytes(msgpack_bytes, GraphData)
    assert deserialized.nodes[0].label == "Binary Node"
    assert deserialized.edges[0].type == "BINARY_LINK"

    # Test orjson JSON serialization
    json_bytes = SerializerEngine.to_json_bytes(graph)
    assert b"Binary Node" in json_bytes
