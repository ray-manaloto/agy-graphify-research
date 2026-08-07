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
    assert metrics_low.recommended_model == "flash"

    # Test over threshold (50% utilization)
    metrics_high = await engine.evaluate_context(estimated_tokens=100000)
    assert metrics_high.requires_subagent_delegation
    assert metrics_high.utilization_percentage == 50.0
    assert metrics_high.recommended_model == "pro"


@pytest.mark.asyncio
async def test_context_input_clamping(tmp_path):
    engine = ContextManagerEngine(project_dir=tmp_path)

    # Negative input
    metrics_neg = await engine.evaluate_context(estimated_tokens=-5000)
    assert metrics_neg.estimated_context_tokens == 0
    assert metrics_neg.utilization_percentage == 0.0

    # Overflow input
    metrics_over = await engine.evaluate_context(estimated_tokens=500000)
    assert metrics_over.utilization_percentage == 100.0
