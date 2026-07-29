"""Async unit tests for EnvironmentVerifier using pytest."""

import pytest

from agy_graphify.models.verification_schema import Decision
from agy_graphify.verify import EnvironmentVerifier


@pytest.mark.asyncio
async def test_environment_verifier_pass(tmp_path):
    # Setup mock project directory with required guardrails and mise toolchain
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir()
    (gemini_dir / "settings.json").write_text("{}", encoding="utf-8")
    rules_dir = gemini_dir / "rules"
    rules_dir.mkdir()
    (rules_dir / "test_rule.md").write_text("# Test Rule", encoding="utf-8")

    mise_file = tmp_path / ".mise.toml"
    mise_content = (
        "[tools]\n"
        'python = "3.14.6"\n'
        'uv = "0.12.0"\n'
        'ruff = "0.15.12"\n'
        'ty = "0.0.32"\n'
        'hk = "1.53.0"\n'
        'fnox = "1.31.1"\n'
        'pkl = "0.32.1"\n'
        'taplo = "0.10.0"\n'
        'gh = "2.96.0"\n'
    )
    mise_file.write_text(mise_content, encoding="utf-8")

    global_gemini = tmp_path / "global_gemini"
    global_gemini.mkdir()
    (global_gemini / "settings.json").write_text("{}", encoding="utf-8")

    verifier = EnvironmentVerifier(project_dir=tmp_path, gemini_dir=global_gemini)
    result = await verifier.run_check()

    assert result.decision == Decision.allow
    assert result.reason is None
