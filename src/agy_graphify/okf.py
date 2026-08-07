"""Open Knowledge Format (OKF) validator and parser for AI/LLM documentation catalog."""

import argparse
import asyncio
from pathlib import Path

from .logger import logger
from .models.verification_schema import Decision, VerificationResult


class OKFValidator:
    """Validates markdown documentation files against the Open Knowledge Format (OKF) spec."""

    def __init__(self, target_dir: Path | None = None) -> None:
        self.target_dir = target_dir or Path.cwd()

    async def validate_file(self, file_path: Path) -> list[str]:
        """Validate a single markdown file for OKF compliance."""
        issues: list[str] = []
        content = file_path.read_text(encoding="utf-8")  # noqa: ASYNC240

        if not content.startswith("---"):
            issues.append(f"{file_path.name}: Missing YAML frontmatter header (---)")
            return issues

        parts = content.split("---", 2)
        if len(parts) < 3:
            issues.append(f"{file_path.name}: Malformed YAML frontmatter")
            return issues

        # Differentiate Antigravity SKILL.md from standard OKF Markdown docs
        if file_path.name == "SKILL.md":
            import yaml

            raw_yaml = yaml.safe_load(parts[1]) or {}
            if "name" not in raw_yaml or "description" not in raw_yaml:
                issues.append(
                    f"{file_path.name}: Missing required skill frontmatter field 'name' or 'description'"
                )
            return issues

        try:
            import yaml
            from pydantic import ValidationError

            from .models.okf_schema import OKFFrontmatter

            raw_yaml = yaml.safe_load(parts[1]) or {}
            OKFFrontmatter.model_validate(raw_yaml)
        except ImportError:
            # Fallback if PyYAML not installed in local environment
            frontmatter_str = parts[1]
            required_keys = ["title", "doc_id", "version", "type"]
            for key in required_keys:
                if f"{key}:" not in frontmatter_str:
                    issues.append(
                        f"{file_path.name}: Missing required OKF frontmatter field '{key}'"
                    )
        except ValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(l) for l in err["loc"])
                issues.append(
                    f"{file_path.name}: Frontmatter validation error in '{loc}': {err['msg']}"
                )

        body = parts[2].strip()
        if not body:
            issues.append(f"{file_path.name}: OKF document body is empty")

        if (
            "## Overview" not in body
            and "## Context" not in body
            and "## Learned Remediation Rules" not in body
        ):
            issues.append(
                f"{file_path.name}: Missing required section '## Overview', '## Context', or '## Learned Remediation Rules'"
            )

        return issues

    async def validate_all(self, docs_dir: Path | None = None) -> VerificationResult:
        """Validate all documentation files in docs/ against OKF spec."""
        target = docs_dir or (self.target_dir / "docs")
        if not target.is_dir():
            logger.info(f"No docs directory found at {target}, skipping OKF check.")
            return VerificationResult(decision=Decision.allow)

        all_issues: list[str] = []
        for file_path in target.glob("**/*.md"):
            issues = await self.validate_file(file_path)
            all_issues.extend(issues)

        # Check LESSONS.md if present at project root
        lessons = self.target_dir / "LESSONS.md"
        if lessons.is_file():
            all_issues.extend(await self.validate_file(lessons))

        if all_issues:
            msg = "OKF documentation validation failed: " + "; ".join(all_issues)
            logger.warning(msg)
            return VerificationResult(decision=Decision.deny, reason=msg)

        logger.info("All documentation files satisfy the Open Knowledge Format (OKF) spec.")
        return VerificationResult(
            decision=Decision.allow,
            additionalContext="OKF Validation passed: Documentation adheres to Open Knowledge Format.",
        )


async def async_main(*params: str) -> None:
    """Async main for OKF CLI runner."""
    parser = argparse.ArgumentParser(description="Open Knowledge Format (OKF) Spec Validator")
    parser.add_argument("path", nargs="?", default="docs", help="Path to docs directory")

    args = parser.parse_args(list(params) if params else [])

    validator = OKFValidator()
    result = await validator.validate_all(docs_dir=Path(args.path))
    print(result.model_dump_json(exclude_none=True))
    if result.decision == Decision.deny:
        raise SystemExit(1)


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
