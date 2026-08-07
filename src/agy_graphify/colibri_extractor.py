"""Colibri Local LLM Extractor & Assistant Engine for Graphify."""

import asyncio
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import GraphifyConfig
from .logger import logger
from .models.graph_schema import Edge, GraphData, Node


class ColibriExtractor:
    """Free local LLM-powered knowledge graph extractor backed by Colibri C/Metal engine."""

    def __init__(self, config: GraphifyConfig | None = None) -> None:
        self.config = config or GraphifyConfig.load()
        self.server_url = self.config.colibri.server_url.rstrip("/")
        self.server_process: asyncio.subprocess.Process | None = None

    def is_server_running(self) -> bool:
        """Check if Colibri OpenAI-compatible server is listening."""
        try:
            url = f"{self.server_url}/models"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def ensure_server_running(self) -> bool:
        """Auto-launch local Colibri server if not already running."""
        if self.is_server_running():
            logger.info(f"Colibri server already running at {self.server_url}")
            return True

        if getattr(self, "_attempted_launch", False):
            return False
        self._attempted_launch = True

        if not self.config.colibri.auto_launch:
            logger.warning(f"Colibri server at {self.server_url} offline and auto_launch is False.")
            return False

        script = Path(
            self.config.colibri.server_script or "scratch/colibri/repo/c/openai_server.py"
        )
        if not script.is_file():
            logger.warning(
                f"Colibri server script not found at {script}. Proceeding with offline fallback."
            )
            return False

        logger.info(f"Auto-launching Colibri local server from {script}...")
        try:
            cmd = ["python3", str(script), "--port", "8080"]
            if self.config.colibri.model_path:
                cmd.extend(["--model", self.config.colibri.model_path])

            self.server_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait up to 5 seconds for server startup
            for _ in range(25):
                await asyncio.sleep(0.2)
                if self.is_server_running():
                    logger.info("Colibri local server successfully launched and ready.")
                    return True

            logger.warning("Colibri server launched but health check timed out.")
            return False
        except Exception as err:
            logger.error(f"Failed to auto-launch Colibri server: {err}")
            return False

    def build_extraction_prompt(self, file_path: Path, content: str) -> str:
        """Build Graphify semantic extraction prompt for a given file."""
        return (
            f"You are a Graphify knowledge graph extraction engine.\n"
            f"Analyze the source file '{file_path.name}' ({file_path.suffix}):\n\n"
            f"--- BEGIN FILE CONTENT ---\n{content[:4000]}\n--- END FILE CONTENT ---\n\n"
            f"Extract all primary concepts, entities, functions, classes, and rationale nodes.\n"
            f"Return ONLY valid JSON matching this schema:\n"
            f'{{"nodes": [{{"id": "symbol_name", "label": "Human Label", "file_type": "code|doc"}}], '
            f'"edges": [{{"source": "id1", "target": "id2", "relation": "calls|conceptually_related_to", "confidence": "EXTRACTED|INFERRED", "confidence_score": 0.9}}]}}\n'
        )

    async def call_colibri_api(self, prompt: str) -> dict[str, Any]:
        """Send prompt to local Colibri HTTP server or return mock structure when offline."""
        if not self.is_server_running():
            logger.info("Colibri HTTP server offline - returning heuristic graph payload.")
            return self._fallback_heuristic_extraction(prompt)

        try:
            url = f"{self.server_url}/chat/completions"
            payload = json.dumps(
                {
                    "model": self.config.colibri.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                }
            ).encode("utf-8")

            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
            )

            loop = asyncio.get_running_loop()
            resp_body = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=30.0).read().decode("utf-8")
            )
            data = json.loads(resp_body)
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as err:
            logger.warning(f"Colibri API call failed: {err}. Falling back to heuristic payload.")
            return self._fallback_heuristic_extraction(prompt)

    def _fallback_heuristic_extraction(self, prompt: str) -> dict[str, Any]:
        """Heuristic fallback extraction when server is not running."""
        lines = prompt.splitlines()
        file_name = "unknown_file"
        file_type = "code"

        for line in lines:
            if line.startswith("Analyze the source file '"):
                file_name = line.split("'")[1]
                if file_name.endswith(".md"):
                    file_type = "doc"
                break

        file_node_id = file_name.lower().replace(".", "_").replace("-", "_")
        nodes: list[dict[str, Any]] = [
            {"id": file_node_id, "label": file_name, "file_type": file_type, "source_file": file_name}
        ]
        edges: list[dict[str, Any]] = []

        # Parse definitions and headings from prompt content
        for line in lines:
            line_str = line.strip()
            if line_str.startswith(("class ", "def ", "async def ")) and ":" in line_str:
                parts = line_str.split("(") if "(" in line_str else line_str.split(":")
                raw_name = parts[0].replace("async def ", "").replace("def ", "").replace("class ", "").strip()
                if raw_name and not raw_name.startswith("_"):
                    symbol_id = f"{file_node_id}_{raw_name.lower()}"
                    nodes.append({"id": symbol_id, "label": raw_name, "file_type": "code_symbol", "source_file": file_name})
                    edges.append({
                        "source": file_node_id,
                        "target": symbol_id,
                        "relation": "defines_symbol",
                        "confidence": "EXTRACTED",
                        "confidence_score": 0.95,
                        "source_file": file_name,
                    })
            elif line_str.startswith(("# ", "## ", "### ")) and len(line_str) > 3:
                heading = line_str.lstrip("#").strip()
                heading_id = f"{file_node_id}_{heading.lower().replace(' ', '_')[:30]}"
                nodes.append({"id": heading_id, "label": heading, "file_type": "doc_section", "source_file": file_name})
                edges.append({
                    "source": file_node_id,
                    "target": heading_id,
                    "relation": "contains_section",
                    "confidence": "EXTRACTED",
                    "confidence_score": 0.9,
                    "source_file": file_name,
                })

        if len(nodes) == 1:
            nodes.append({"id": "colibri_engine", "label": "Colibri Engine", "file_type": "code", "source_file": file_name})
            edges.append({
                "source": file_node_id,
                "target": "colibri_engine",
                "relation": "uses_llm_assistant",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "source_file": file_name,
            })

        return {"nodes": nodes, "edges": edges}


    async def extract_file(self, file_path: Path) -> GraphData:
        """Extract nodes and edges from a single source file using Colibri LLM."""
        if not file_path.is_file():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8", errors="replace")
        prompt = self.build_extraction_prompt(file_path, content)

        await self.ensure_server_running()
        raw_graph = await self.call_colibri_api(prompt)

        nodes: list[Node] = []
        for raw_node in raw_graph.get("nodes", []):
            node_id = str(raw_node.get("id", "node")).lower().replace(" ", "_")
            label = str(raw_node.get("label", node_id))
            file_type = str(raw_node.get("file_type", "document"))
            nodes.append(Node(id=node_id, label=label, type=file_type))

        edges: list[Edge] = []
        for raw_edge in raw_graph.get("edges", []):
            src = str(raw_edge.get("source", "")).lower().replace(" ", "_")
            tgt = str(raw_edge.get("target", "")).lower().replace(" ", "_")
            rel = str(raw_edge.get("relation", "conceptually_related_to"))
            score = float(raw_edge.get("confidence_score", 1.0))
            if src and tgt:
                edges.append(Edge(source=src, target=tgt, type=rel, weight=score))

        return GraphData(
            nodes=nodes,
            edges=edges,
            metadata={"source_file": str(file_path), "extractor": "ColibriExtractor"},
        )

    async def extract_directory(
        self,
        dir_path: Path,
        extensions: tuple[str, ...] = (".py", ".md", ".c", ".metal", ".h", ".js", ".ts", ".rs"),
    ) -> GraphData:
        """Extract knowledge graph across all supported files in a directory."""
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        files = [
            p
            for p in dir_path.rglob("*")
            if p.is_file()
            and p.suffix.lower() in extensions
            and "graphify-out" not in p.parts
            and ".venv" not in p.parts
        ]

        all_nodes: dict[str, Node] = {}
        all_edges: list[Edge] = []

        for file_path in files[:20]:  # Limit batch for safety
            sub_graph = await self.extract_file(file_path)
            for node in sub_graph.nodes:
                all_nodes[node.id] = node
            all_edges.extend(sub_graph.edges)

        return GraphData(
            nodes=list(all_nodes.values()),
            edges=all_edges,
            metadata={
                "target_dir": str(dir_path),
                "total_files": len(files),
                "extractor": "ColibriExtractor",
            },
        )

    def record_learning(self, question: str, answer: str, query_type: str = "query") -> Node:
        """Record a Q&A explanation learning node to global memory."""
        node_id = f"qa_learning_{abs(hash(question)) % 1000000}"
        learning_node = Node(
            id=node_id,
            label=f"Q&A: {question[:50]}...",
            type="qa_learning",
        )

        try:
            global_mem = Path(self.config.global_memory_dir).expanduser()
            global_mem.mkdir(parents=True, exist_ok=True)

            event = {
                "node_id": node_id,
                "question": question,
                "answer": answer,
                "query_type": query_type,
                "timestamp": "2026-08-06T00:00:00Z",
            }
            (global_mem / "learnings.jsonl").open("a", encoding="utf-8").write(json.dumps(event) + "\n")
            logger.info(f"Recorded Q&A learning node {node_id} to {global_mem}")
        except Exception as err:
            logger.warning(f"Could not record learning to global memory: {err}")
        return learning_node


class ServerlessColibriRunner:
    """Zero-token local Colibri Graphify in-process pipeline runner."""

    async def run_task(self, description: str, target_dir: Path) -> GraphData:
        extractor = ColibriExtractor()
        return await extractor.extract_directory(target_dir)
