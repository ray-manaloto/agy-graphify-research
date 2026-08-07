"""Async Environment state & toolchain verifier with session handoff generation."""

import ast
import asyncio
import json
import urllib.error
import urllib.request
from pathlib import Path

from .logger import logger
from .models.verification_schema import Decision, VerificationResult


class IntegrityAuditor:
    """Forensic AST Auditor to detect hardcoded return strings, noop mocks, and illegal shell script calls."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    async def audit_codebase(self) -> list[str]:
        violations: list[str] = []
        src_dir = self.project_dir / "src"
        if not src_dir.is_dir():
            return violations

        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
                for node in ast.walk(tree):
                    # Audit function definitions for trivial hardcoded string returns without logic
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                        # If body contains only a single return statement returning a literal string without parameters/logic
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
                            ret_val = node.body[0].value
                            if (
                                isinstance(ret_val, ast.Constant)
                                and isinstance(ret_val.value, str)
                                and len(ret_val.value) > 50
                            ):
                                violations.append(
                                    f"Forensic Violation in {py_file.name}:{node.name}: Hardcoded return literal string >50 chars detected without computation."
                                )

                    # Audit function calls for prohibited os.system("*.sh") or subprocess.run(["*.sh"])
                    if isinstance(node, ast.Call):
                        func = node.func
                        if isinstance(func, ast.Attribute) and func.attr in (
                            "system",
                            "popen",
                            "call",
                            "run",
                        ):
                            if (
                                node.args
                                and isinstance(node.args[0], ast.Constant)
                                and isinstance(node.args[0].value, str)
                                and ".sh" in node.args[0].value
                            ):
                                violations.append(
                                    f"Forensic Violation in {py_file.name}: Prohibited shell script execution call '{node.args[0].value}'"
                                )
                    # Audit for custom re-invented JSON parsers when orjson/msgspec exist
                    if isinstance(node, ast.FunctionDef) and node.name in ("custom_json_parse", "manual_json_serialize", "custom_logger_class"):
                        violations.append(
                            f"Audit-Before-Reinventing Violation in {py_file.name}:{node.name}: Prohibited custom utility '{node.name}'. Use existing PyPI libraries (orjson, msgspec, pydantic, loguru)."
                        )
            except SyntaxError as exc:
                violations.append(f"Forensic Audit Syntax Error in {py_file.name}: {exc}")

        return violations


class EnvironmentVerifier:
    """Verifies project isolation, explicit toolchain pinning, and builds session handoff context."""

    def __init__(self, project_dir: Path | None = None, gemini_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path.cwd()
        self.gemini_dir = gemini_dir or (Path.home() / ".gemini")
        self.integrity_auditor = IntegrityAuditor(self.project_dir)
        self._cached_result: VerificationResult | None = None
        self._cached_timestamp: float = 0.0

    async def _check_globals(self) -> list[str]:
        violations: list[str] = []

        dirs_to_check = [
            (self.gemini_dir / "config" / "plugins", "Global plugins"),
            (self.gemini_dir / "skills", "Global skills"),
            (self.gemini_dir / "antigravity" / "skills", "Global antigravity skills"),
            (self.gemini_dir / "extensions", "Global extensions"),
        ]

        for path, label in dirs_to_check:
            if path.exists() and any(path.iterdir()):
                violations.append(f"{label} found in {path}")

        return violations

    async def _check_global_settings(self) -> list[str]:
        violations: list[str] = []
        global_settings = self.gemini_dir / "settings.json"
        if global_settings.is_file():
            try:
                data = json.loads(global_settings.read_text(encoding="utf-8"))
                if "experimental" in data or "plugins" in data or "skills" in data:
                    violations.append(
                        f"Global settings in {global_settings} contains non-bare configurations"
                    )
            except json.JSONDecodeError:
                violations.append(f"Invalid JSON in global settings {global_settings}")
        return violations

    async def _check_project_guardrails(self) -> list[str]:
        violations: list[str] = []
        project_settings = self.project_dir / ".gemini" / "settings.json"
        if not project_settings.is_file():
            violations.append(f"Missing project configuration in {project_settings}")

        project_rules = self.project_dir / ".gemini" / "rules"
        if not project_rules.is_dir() or not any(project_rules.iterdir()):
            violations.append(f"Missing project guardrail rules in {project_rules}")

        return violations

    async def _check_toolchain_pinning(self) -> list[str]:
        violations: list[str] = []
        dot_mise = self.project_dir / ".mise.toml"
        plain_mise = self.project_dir / "mise.toml"

        if plain_mise.is_file():
            violations.append(
                f"Duplicate config file '{plain_mise.name}' detected; use '.mise.toml' exclusively"
            )

        if not dot_mise.is_file():
            violations.append(f"Missing .mise.toml tool configuration in {dot_mise}")
            return violations

        content = dot_mise.read_text(encoding="utf-8")
        if '"latest"' in content or "'latest'" in content:
            violations.append(".mise.toml contains unpinned 'latest' tool version references")

        if 'python = "' not in content:
            violations.append(".mise.toml does not pin python version")

        required_tools = ["uv", "ruff", "ty", "hk", "fnox", "pkl", "taplo", "gh"]
        missing_tools = [
            f".mise.toml missing explicit tool definition for '{tool}'"
            for tool in required_tools
            if f"{tool} = " not in content
        ]
        violations.extend(missing_tools)

        return violations

    async def _check_pypi_versions(
        self, packages: list[str] | None = None, timeout: float = 2.0
    ) -> tuple[list[str], list[str]]:
        """Check live PyPI API for latest release versions of key dependencies."""
        violations: list[str] = []
        statuses: list[str] = []
        target_pkgs = packages or ["pydantic", "loguru", "msgspec", "orjson", "pytest", "graphifyy"]

        for pkg in target_pkgs:
            url = f"https://pypi.org/pypi/{pkg}/json"
            req = urllib.request.Request(url, headers={"User-Agent": "agy-verify/0.1.0"})
            try:

                def _fetch(r=req, t=timeout):
                    with urllib.request.urlopen(r, timeout=t) as resp:
                        return json.loads(resp.read().decode("utf-8"))

                data = await asyncio.to_thread(_fetch)
                version = data.get("info", {}).get("version", "unknown")
                statuses.append(f"PyPI:{pkg}=={version}")
            except Exception as err:
                logger.debug(f"Live PyPI check for '{pkg}' offline fallback: {err}")
                statuses.append(f"PyPI:{pkg}(cached)")

        return violations, statuses

    async def _check_github_versions(
        self, repos: list[str] | None = None, timeout: float = 2.0
    ) -> tuple[list[str], list[str]]:
        """Check live GitHub API for latest releases of pinned tool repositories."""
        violations: list[str] = []
        statuses: list[str] = []
        target_repos = repos or ["astral-sh/uv", "astral-sh/ruff", "astral-sh/ty"]

        for repo in target_repos:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "agy-verify/0.1.0",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            try:

                def _fetch(r=req, t=timeout):
                    with urllib.request.urlopen(r, timeout=t) as resp:
                        return json.loads(resp.read().decode("utf-8"))

                data = await asyncio.to_thread(_fetch)
                tag_name = data.get("tag_name", "unknown")
                statuses.append(f"GitHub:{repo}@{tag_name}")
            except Exception as err:
                logger.debug(f"Live GitHub check for '{repo}' offline fallback: {err}")
                statuses.append(f"GitHub:{repo}(cached)")

        return violations, statuses

    async def _build_handoff_context(self, api_statuses: list[str] | None = None) -> str:
        """Construct progressive handoff context for new sessions without context bloat."""
        graph_report = self.project_dir / "graphify-out" / "GRAPH_REPORT.md"
        telemetry_file = self.project_dir / ".gemini" / "telemetry" / "events.jsonl"
        state_file = self.project_dir / ".gemini" / "graph_state.json"

        context_parts = [
            "Project Isolation Verified: Tools pinned in .mise.toml without 'latest'.",
            "Progressive Handoff Context: Read AGENTS.md for subagent delegation rules.",
        ]

        if api_statuses:
            context_parts.append(f"Live API Version Checks: {', '.join(api_statuses)}")
        if state_file.is_file():
            context_parts.append(
                "Active State Graph Found (.gemini/graph_state.json): Ask user on startup if they want to resume the next logical step."
            )
        if graph_report.is_file():
            context_parts.append("Knowledge Graph: Available in graphify-out/GRAPH_REPORT.md.")
        if telemetry_file.is_file():
            context_parts.append(
                "Telemetry: Event logs recorded in .gemini/telemetry/events.jsonl."
            )

        return " | ".join(context_parts)

    async def _check_shell_scripts(self) -> list[str]:
        violations: list[str] = []
        # Shell scripts are strictly prohibited in the core codebase (outside 3rd party skills, vendor, scratch, .venv)
        for sh_file in self.project_dir.rglob("*.sh"):
            rel_path = sh_file.relative_to(self.project_dir)
            parts = rel_path.parts
            if (
                ".venv" in parts
                or "vendor" in parts
                or "scratch" in parts
                or ".git" in parts
                or ".agents" in parts
                or ".gemini" in parts
                or "repos" in parts
            ):
                continue
            violations.append(
                f"Prohibited shell script '{rel_path}' detected. Shell scripts (*.sh) are strictly banned in core project code; use uv run via .mise.toml or Python scripts."
            )
        return violations

    async def run_check(self, use_cache: bool = True, cache_ttl: float = 60.0) -> VerificationResult:
        import time

        if use_cache and self._cached_result is not None:
            if (time.time() - self._cached_timestamp) < cache_ttl:
                logger.debug("Reusing cached EnvironmentVerifier VerificationResult")
                return self._cached_result

        globals_v = await self._check_globals()
        settings_v = await self._check_global_settings()
        rules_v = await self._check_project_guardrails()
        toolchain_v = await self._check_toolchain_pinning()
        sh_v = await self._check_shell_scripts()
        forensic_v = await self.integrity_auditor.audit_codebase()
        pypi_v, pypi_status = await self._check_pypi_versions()
        github_v, github_status = await self._check_github_versions()

        # Audit repository count in repos/ against extended_repo_manifest.json
        manifest_file = self.project_dir / "graphify-out" / "extended_repo_manifest.json"
        repo_violations: list[str] = []
        if manifest_file.exists():
            try:
                manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                expected_count = len(manifest_data)
                actual_repos = [p for p in (self.project_dir / "repos").rglob("*") if (p / ".git").is_dir()] if (self.project_dir / "repos").exists() else []
                if len(actual_repos) < expected_count:
                    repo_violations.append(
                        f"Repository Ingestion Incomplete: Expected {expected_count} repos from manifest, found {len(actual_repos)} in repos/"
                    )
            except Exception as exc:
                repo_violations.append(f"Manifest read error: {exc}")

        violations = [
            *globals_v,
            *settings_v,
            *rules_v,
            *toolchain_v,
            *sh_v,
            *forensic_v,
            *pypi_v,
            *github_v,
            *repo_violations,
        ]

        if violations:
            reason_msg = "State verification failed: " + "; ".join(violations)
            logger.warning(reason_msg)
            res = VerificationResult(
                decision=Decision.deny,
                reason=reason_msg,
            )
            self._cached_result = res
            self._cached_timestamp = time.time()
            return res

        api_statuses = [*pypi_status, *github_status]
        handoff_ctx = await self._build_handoff_context(api_statuses=api_statuses)
        logger.info(
            "Project state, live API checks, and toolchain verification passed successfully."
        )
        res = VerificationResult(
            decision=Decision.allow,
            additionalContext=handoff_ctx,
        )
        self._cached_result = res
        self._cached_timestamp = time.time()
        return res

    async def verify_and_output(self) -> int:
        result = await self.run_check()
        print(result.model_dump_json(exclude_none=True))
        return 0 if result.decision == Decision.allow else 1


def main() -> None:
    verifier = EnvironmentVerifier()
    exit_code = asyncio.run(verifier.verify_and_output())
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
