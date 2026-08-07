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


@pytest.mark.asyncio
async def test_integrity_auditor_hardcoded_literal(tmp_path):
    from agy_graphify.verify import IntegrityAuditor

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    bad_py = src_dir / "bad_code.py"
    # Function returning literal string > 50 chars without computation
    bad_py.write_text(
        "def fake_function():\n"
        '    return "This is a super long hardcoded string literal that is returned directly without any computation or variable calculation."\n',
        encoding="utf-8",
    )

    auditor = IntegrityAuditor(project_dir=tmp_path)
    violations = await auditor.audit_codebase()
    assert len(violations) == 1
    assert "Hardcoded return literal string >50 chars detected" in violations[0]


@pytest.mark.asyncio
async def test_live_api_version_checks(tmp_path):
    verifier = EnvironmentVerifier(project_dir=tmp_path)
    violations, pypi_status = await verifier._check_pypi_versions(["pydantic"])
    assert isinstance(violations, list)
    assert len(pypi_status) == 1
    assert "PyPI:pydantic" in pypi_status[0]

    violations, gh_status = await verifier._check_github_versions(["astral-sh/uv"])
    assert isinstance(violations, list)
    assert len(gh_status) == 1
    assert "GitHub:astral-sh/uv" in gh_status[0]
