"""Async unit tests for ContextManagerEngine using pytest."""

import pytest

from agy_graphify.context_manager import ContextManagerEngine


@pytest.mark.asyncio
async def test_context_evaluation(tmp_path):
    engine = ContextManagerEngine(project_dir=tmp_path)

    # Test under threshold (20% utilization)
    metrics_low = await engine.evaluate_context(estimated_tokens=40000)
    assert not metrics_low.requires_subagent_delegation
    assert metrics_low.utilization_percentage == 20.0

    # Test over threshold (50% utilization)
    metrics_high = await engine.evaluate_context(estimated_tokens=100000)
    assert metrics_high.requires_subagent_delegation
    assert metrics_high.utilization_percentage == 50.0
