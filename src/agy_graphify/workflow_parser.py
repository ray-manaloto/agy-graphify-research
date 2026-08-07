"""OpenAI Symphony Workflow Spec Parser for StateGraphEngine schemas."""

from pathlib import Path

from .models.graph_engine_schema import (
    GraphEngineSchema,
    Node,
    Status,
    Status1,
    SymphonyWorkflowSpec,
)


class SymphonyWorkflowParser:
    """Parses declarative OpenAI Symphony YAML specs into StateGraphEngine schemas."""

    @staticmethod
    def parse_yaml_str(yaml_content: str) -> GraphEngineSchema:
        import yaml

        raw_dict = yaml.safe_load(yaml_content) or {}
        spec = SymphonyWorkflowSpec.model_validate(raw_dict)
        return SymphonyWorkflowParser.to_graph_schema(spec)

    @staticmethod
    def parse_yaml_file(file_path: Path | str) -> GraphEngineSchema:
        path = Path(file_path) if isinstance(file_path, str) else file_path
        content = path.read_text(encoding="utf-8")
        return SymphonyWorkflowParser.parse_yaml_str(content)

    @staticmethod
    def to_graph_schema(spec: SymphonyWorkflowSpec) -> GraphEngineSchema:
        nodes = []
        for n_spec in spec.nodes:
            node = Node(
                id=n_spec.id,
                node_type=n_spec.node_type,
                status=Status1.pending,
                dependencies=n_spec.dependencies or None,
                subagent_role=n_spec.role,
                task_action=n_spec.instructions,
            )
            nodes.append(node)
        return GraphEngineSchema(
            graph_id=spec.name,
            execution_mode=spec.execution_mode,
            status=Status.pending,
            remediation_count=0,
            max_remediations=spec.max_remediations,
            nodes=nodes,
        )
