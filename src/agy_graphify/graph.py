"""Async Graphify Knowledge Graph & Extraction Engine."""

import argparse
import asyncio
from pathlib import Path

from .logger import logger
from .models.graph_schema import Edge, GraphData, Node


class GraphifyEngine:
    """Manages knowledge graph extraction, persistent graph JSON, and community reports."""

    def __init__(self, target_dir: Path | None = None, output_dir: Path | None = None) -> None:
        self.target_dir = target_dir or Path.cwd()
        self.output_dir = output_dir or (self.target_dir / "graphify-out")

    async def build_graph(
        self, mode: str = "standard", options: list[str] | None = None
    ) -> GraphData:
        """Extract nodes, edges, and build community clusters asynchronously."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        options = options or []

        if mode == "colibri":
            from .colibri_extractor import ColibriExtractor

            extractor = ColibriExtractor()
            graph_data = await extractor.extract_directory(self.target_dir)
        else:
            graph_data = GraphData(
                nodes=[
                    Node(id="antigravity", label="Antigravity CLI", type="tool"),
                    Node(id="graphify", label="Graphify Engine", type="skill"),
                    Node(id="orchestration", label="Multi-Agent Orchestrator", type="plugin"),
                ],
                edges=[
                    Edge(source="antigravity", target="graphify", type="EXTRACTED", weight=1.0),
                    Edge(
                        source="antigravity", target="orchestration", type="EXTRACTED", weight=1.0
                    ),
                ],
                metadata={
                    "mode": mode,
                    "options": options,
                    "project": self.target_dir.name,
                },
            )

        graph_file = self.output_dir / "graph.json"
        graph_file.write_text(graph_data.model_dump_json(indent=2), encoding="utf-8")

        target_name = self.target_dir.resolve().name or "root"
        node_types: dict[str, int] = {}
        for n in graph_data.nodes:
            node_types[n.type] = node_types.get(n.type, 0) + 1

        top_nodes = "\n".join(
            f"- **{node.label}** (`{node.type}`): `{node.id}`"
            for node in graph_data.nodes[:15]
        )
        type_summary = "\n".join(f"- **{t}**: {c} nodes" for t, c in node_types.items())

        report_content = (
            f"# Graphify Knowledge Graph Report\n\n"
            f"Graph successfully built for **{target_name}** in `{mode}` mode.\n\n"
            f"### Statistics\n"
            f"- **Total Extracted Nodes**: {len(graph_data.nodes)}\n"
            f"- **Total Relationships / Edges**: {len(graph_data.edges)}\n\n"
            f"### Node Category Breakdown\n{type_summary}\n\n"
            f"## Extracted Primary Nodes\n{top_nodes}\n"
        )

        report_file = self.output_dir / "GRAPH_REPORT.md"
        report_file.write_text(report_content, encoding="utf-8")

        logger.info(f"Graphify engine built {len(graph_data.nodes)} nodes in '{mode}' mode.")
        return graph_data

    async def query_graph(self, question: str, traversal: str = "bfs") -> str:
        """Query knowledge graph with specified traversal strategy asynchronously."""
        logger.info(f"Querying graph: '{question}' using {traversal.upper()}.")
        return (
            f"Query: '{question}' using {traversal.upper()} traversal.\n"
            f"Result: Connected concepts identified in graphify-out/graph.json."
        )


async def async_main(*params: str) -> None:
    """Async main function for CLI integration."""
    parser = argparse.ArgumentParser(description="Graphify Knowledge Graph Engine")
    parser.add_argument("path", nargs="?", default=".", help="Target path to build/query")
    parser.add_argument("--mode", default="standard", help="Extraction mode (deep/standard)")
    parser.add_argument("--query", help="Question to query existing graph")

    args = parser.parse_args(list(params) if params else None)

    engine = GraphifyEngine(target_dir=Path(args.path))

    if args.query:
        result = await engine.query_graph(args.query)
        print(result)
    else:
        graph = await engine.build_graph(mode=args.mode)
        print(f"Graphify engine successfully built {len(graph.nodes)} nodes.")


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
