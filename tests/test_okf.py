"""Async unit tests for Open Knowledge Format (OKF) specification validation."""

from pathlib import Path

import pytest

from agy_graphify.models.verification_schema import Decision
from agy_graphify.okf import OKFValidator


@pytest.mark.asyncio
async def test_okf_valid_document(tmp_path: Path) -> None:
    doc = tmp_path / "valid.md"
    doc.write_text(
        "---\n"
        "title: Test Guide\n"
        "doc_id: okf-test-guide-001\n"
        "version: 1.0.0\n"
        "type: guide\n"
        "status: approved\n"
        "---\n\n"
        "# Test Guide\n\n"
        "## Overview\n\n"
        "This is a valid OKF document.\n",
        encoding="utf-8",
    )

    validator = OKFValidator(target_dir=tmp_path)
    issues = await validator.validate_file(doc)
    assert len(issues) == 0


@pytest.mark.asyncio
async def test_okf_missing_frontmatter(tmp_path: Path) -> None:
    doc = tmp_path / "invalid.md"
    doc.write_text("# Title Without Frontmatter\n\n## Overview\n", encoding="utf-8")

    validator = OKFValidator(target_dir=tmp_path)
    issues = await validator.validate_file(doc)
    assert len(issues) > 0
    assert "Missing YAML frontmatter header" in issues[0]


@pytest.mark.asyncio
async def test_okf_missing_required_fields(tmp_path: Path) -> None:
    doc = tmp_path / "missing_fields.md"
    doc.write_text(
        "---\ntitle: Incomplete Doc\n---\n\n## Overview\n",
        encoding="utf-8",
    )

    validator = OKFValidator(target_dir=tmp_path)
    issues = await validator.validate_file(doc)
    assert len(issues) > 0


@pytest.mark.asyncio
async def test_okf_invalid_doc_id_regex(tmp_path: Path) -> None:
    doc = tmp_path / "bad_id.md"
    doc.write_text(
        "---\n"
        "title: Bad ID\n"
        "doc_id: BAD_ID_UPPERCASE\n"
        "version: 1.0.0\n"
        "type: report\n"
        "---\n\n"
        "## Overview\n",
        encoding="utf-8",
    )

    validator = OKFValidator(target_dir=tmp_path)
    issues = await validator.validate_file(doc)
    assert len(issues) > 0


@pytest.mark.asyncio
async def test_okf_validate_all_docs() -> None:
    validator = OKFValidator()
    result = await validator.validate_all()
    assert result.decision == Decision.allow
