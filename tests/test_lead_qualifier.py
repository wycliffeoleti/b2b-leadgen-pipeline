"""Tests for lead qualification processor."""

import pytest

from first_agentic_workflow.cost_tracker import CostTracker
from first_agentic_workflow.processors.lead_qualifier import LeadQualifier, _extract_json


class TestExtractJson:
    def test_plain_json(self):
        result = _extract_json('{"score": 85, "recommended_action": "pursue"}')
        assert result["score"] == 85

    def test_json_in_code_block(self):
        text = '```json\n{"score": 90, "recommended_action": "nurture"}\n```'
        result = _extract_json(text)
        assert result["score"] == 90

    def test_json_in_bare_code_block(self):
        text = '```\n{"score": 70, "recommended_action": "skip"}\n```'
        result = _extract_json(text)
        assert result["score"] == 70

    def test_json_with_surrounding_text(self):
        text = 'Here is my analysis:\n{"score": 60, "recommended_action": "nurture"}\nDone.'
        result = _extract_json(text)
        assert result["score"] == 60


class TestLeadQualifierDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_returns_dummy(self, sample_raw_lead):
        tracker = CostTracker(budget_usd=1.0)
        qualifier = LeadQualifier(cost_tracker=tracker, dry_run=True)
        result = await qualifier.qualify(sample_raw_lead)

        assert result.score == 50
        assert result.recommended_action == "nurture"
        assert "dry run" in result.qualification_reasoning.lower()
        assert tracker.total_cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_dry_run_batch(self, sample_raw_lead):
        tracker = CostTracker(budget_usd=1.0)
        qualifier = LeadQualifier(cost_tracker=tracker, dry_run=True)
        results = await qualifier.qualify_batch([sample_raw_lead, sample_raw_lead])

        assert len(results) == 2
        assert all(r.score == 50 for r in results)
