"""Centralized repository registry with Git SHA differential tracking and graph coverage auditing."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from agy_graphify.logger import setup_universal_logging, logger

setup_universal_logging()

CONFIG_DIR = Path("config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = CONFIG_DIR / "sources.json"
STATE_FILE = Path(".gemini") / "commit_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
REPOS_BASE = Path("repos")

class SourceRegistryManager:
    """Manages git repository updates, commit SHA state, delta tracking, and graph coverage auditing."""

    def __init__(self) -> None:
        self.state: dict[str, str] = self._load_state()

    def _load_state(self) -> dict[str, str]:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Could not load commit state: {e}")
        return {}

    def _save_state(self) -> None:
        STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        logger.info(f"Saved commit state for {len(self.state)} repositories to {STATE_FILE}")

    def get_repo_commit(self, repo_path: Path) -> str | None:
        """Get current git commit SHA for a repository."""
        if not (repo_path / ".git").is_dir():
            return None
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
        return None

    def sync_and_get_deltas(self, manifest_path: Path | None = None) -> list[dict[str, Any]]:
        """Sync all repos and return only changed/delta repositories since last run."""
        target_manifest = manifest_path or (Path("graphify-out") / "extended_repo_manifest.json")
        if not target_manifest.exists():
            logger.error(f"Manifest {target_manifest} not found.")
            return []

        manifest: list[dict[str, Any]] = json.loads(target_manifest.read_text(encoding="utf-8"))
        logger.info(f"Syncing {len(manifest)} repositories from registry...")

        deltas: list[dict[str, Any]] = []
        unchanged = 0

        for item in manifest:
            repo_path = Path(item["path"])
            repo_key = f"{item['owner']}/{item['name']}".lower()

            if not repo_path.exists():
                continue

            current_sha = self.get_repo_commit(repo_path)
            last_sha = self.state.get(repo_key)

            if current_sha and current_sha == last_sha:
                unchanged += 1
            else:
                logger.info(f"Delta detected for {repo_key}: {last_sha or 'NEW'} -> {current_sha}")
                deltas.append(item)
                if current_sha:
                    self.state[repo_key] = current_sha

        self._save_state()
        logger.info(f"Git SHA Differential Sync: {len(deltas)} deltas detected, {unchanged} repos unchanged.")
        return deltas

    def audit_graph_coverage(self, manifest_path: Path | None = None, graph_path: Path | None = None) -> list[dict[str, Any]]:
        """Audit graph.json and return repositories in manifest that are missing from graph.json."""
        m_path = manifest_path or (Path("graphify-out") / "extended_repo_manifest.json")
        g_path = graph_path or (Path("graphify-out") / "graph.json")

        if not m_path.exists() or not g_path.exists():
            logger.error(f"Manifest ({m_path}) or Graph ({g_path}) missing.")
            return []

        manifest: list[dict[str, Any]] = json.loads(m_path.read_text(encoding="utf-8"))
        graph_data: dict[str, Any] = json.loads(g_path.read_text(encoding="utf-8"))
        nodes: list[dict[str, Any]] = graph_data.get("nodes", [])

        repos_in_graph: set[str] = set()
        for n in nodes:
            label = n.get("label", "")
            match = re.search(r"\(([^)]+)\)$", label)
            if match:
                repos_in_graph.add(match.group(1).lower())
            n_id = n.get("id", "").lower()
            for item in manifest:
                name_clean = item["name"].lower().replace("-", "_")
                if name_clean in n_id or item["name"].lower() in label.lower():
                    repos_in_graph.add(item["name"].lower())

        missing: list[dict[str, Any]] = []
        for item in manifest:
            repo_name = item["name"].lower()
            if repo_name not in repos_in_graph:
                missing.append(item)

        logger.info(f"Graph Coverage Audit: {len(manifest) - len(missing)}/{len(manifest)} repos in graph. {len(missing)} missing.")
        return missing


def update_all_sources() -> None:
    """CLI Entrypoint to sync repositories, update commit SHA differential state, and audit graph coverage."""
    mgr = SourceRegistryManager()
    mgr.sync_and_get_deltas()
    mgr.audit_graph_coverage()


__all__ = ["SourceRegistryManager", "update_all_sources"]
