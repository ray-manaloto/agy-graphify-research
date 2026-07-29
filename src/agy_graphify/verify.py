"""Async Environment state & toolchain verifier for Antigravity/Gemini projects."""

import asyncio
import json
from pathlib import Path

from .logger import logger
from .models.verification_schema import Decision, VerificationResult


class EnvironmentVerifier:
    """Verifies project isolation, environment cleanliness, and explicit toolchain pinning."""

    def __init__(self, project_dir: Path | None = None, gemini_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path.cwd()
        self.gemini_dir = gemini_dir or (Path.home() / ".gemini")

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

        if 'python = "3.14.6"' not in content:
            violations.append('.mise.toml does not pin python = "3.14.6"')

        required_tools = ["uv", "ruff", "ty", "hk", "fnox", "pkl", "taplo", "gh"]
        missing_tools = [
            f".mise.toml missing explicit tool definition for '{tool}'"
            for tool in required_tools
            if f"{tool} = " not in content
        ]
        violations.extend(missing_tools)

        return violations

    async def run_check(self) -> VerificationResult:
        globals_v = await self._check_globals()
        settings_v = await self._check_global_settings()
        rules_v = await self._check_project_guardrails()
        toolchain_v = await self._check_toolchain_pinning()

        violations = [*globals_v, *settings_v, *rules_v, *toolchain_v]

        if violations:
            reason_msg = "State verification failed: " + "; ".join(violations)
            logger.warning(reason_msg)
            return VerificationResult(
                decision=Decision.deny,
                reason=reason_msg,
            )

        logger.info("Project state and toolchain verification passed successfully.")
        return VerificationResult(
            decision=Decision.allow,
            additionalContext=(
                "Project isolation verified: All plugins, skills, rules, settings, and "
                "explicit toolchain versions strictly originate from this project."
            ),
        )

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
