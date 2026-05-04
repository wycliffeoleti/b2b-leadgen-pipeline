"""Tests for cost tracking and budget enforcement."""

import pytest

from first_agentic_workflow.cost_tracker import CostTracker
from first_agentic_workflow.exceptions import BudgetExceededError


class TestCostTracker:
    def test_initial_state(self):
        tracker = CostTracker(budget_usd=1.0)
        assert tracker.total_cost_usd == 0.0
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0

    def test_record_accumulates(self):
        tracker = CostTracker(budget_usd=1.0)
        tracker.record(input_tokens=1000, output_tokens=500, model="gemini-2.0-flash")
        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
        assert tracker.total_cost_usd > 0

        tracker.record(input_tokens=2000, output_tokens=1000, model="gemini-2.0-flash")
        assert tracker.total_input_tokens == 3000
        assert tracker.total_output_tokens == 1500

    def test_gemini_flash_pricing(self):
        tracker = CostTracker(budget_usd=10.0)
        # 1M input tokens at $0.10, 1M output tokens at $0.40
        tracker.record(input_tokens=1_000_000, output_tokens=1_000_000, model="gemini-2.0-flash")
        assert abs(tracker.total_cost_usd - 0.50) < 0.001

    def test_budget_exceeded(self):
        tracker = CostTracker(budget_usd=0.0001)
        with pytest.raises(BudgetExceededError, match="Budget exceeded"):
            tracker.record(
                input_tokens=1_000_000, output_tokens=1_000_000, model="gemini-2.0-flash"
            )

    def test_budget_not_exceeded(self):
        tracker = CostTracker(budget_usd=10.0)
        tracker.record(input_tokens=1000, output_tokens=500, model="gemini-2.0-flash")
        # Should not raise

    def test_unknown_model_uses_default(self):
        tracker = CostTracker(budget_usd=10.0)
        tracker.record(input_tokens=1000, output_tokens=500, model="unknown-model")
        assert tracker.total_cost_usd > 0
