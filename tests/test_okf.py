"""Async unit tests for OKFValidator using pytest."""

import pytest

from agy_graphify.models.verification_schema import Decision
from agy_graphify.okf import OKFValidator


@pytest.mark.asyncio
async def test_okf_validator_pass(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    okf_doc = docs_dir / "valid_doc.md"
    okf_doc.write_text(
        "---\n"
        "title: Test Doc\n"
        "doc_id: okf-001\n"
        "version: 1.0.0\n"
        "type: guide\n"
        "---\n\n"
        "# Test Doc\n\n"
        "## Overview\n\n"
        "This is an OKF compliant document.\n",
        encoding="utf-8",
    )

    validator = OKFValidator(target_dir=tmp_path)
    result = await validator.validate_all(docs_dir=docs_dir)

    assert result.decision == Decision.allow
    assert result.reason is None
