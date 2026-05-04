"""Tests for domain models."""

from datetime import datetime

import pytest

from first_agentic_workflow.models import QualifiedLead, RawLead, SearchCriteria, WorkflowResult


class TestSearchCriteria:
    def test_defaults(self):
        c = SearchCriteria(industry="SaaS", location="Austin")
        assert c.company_size_min == 1
        assert c.company_size_max == 10000
        assert c.keywords == []

    def test_full(self):
        c = SearchCriteria(
            industry="SaaS",
            location="Austin",
            company_size_min=10,
            company_size_max=200,
            keywords=["B2B", "startup"],
        )
        assert c.industry == "SaaS"
        assert c.keywords == ["B2B", "startup"]


class TestRawLead:
    def test_minimal(self):
        lead = RawLead(company_name="Acme", source_url="https://example.com")
        assert lead.company_name == "Acme"
        assert lead.website is None
        assert lead.employee_count is None
        assert isinstance(lead.scraped_at, datetime)

    def test_full(self, sample_raw_lead):
        assert sample_raw_lead.contact_name == "Jane Smith"
        assert sample_raw_lead.employee_count == 45


class TestQualifiedLead:
    def test_score_bounds(self, sample_raw_lead):
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            QualifiedLead(
                raw=sample_raw_lead,
                score=-1,
                qualification_reasoning="test",
                recommended_action="skip",
            )

        with pytest.raises(ValueError, match="less than or equal to 100"):
            QualifiedLead(
                raw=sample_raw_lead,
                score=101,
                qualification_reasoning="test",
                recommended_action="skip",
            )

    def test_valid_actions(self, sample_raw_lead):
        for action in ("pursue", "nurture", "skip"):
            lead = QualifiedLead(
                raw=sample_raw_lead,
                score=50,
                qualification_reasoning="test",
                recommended_action=action,
            )
            assert lead.recommended_action == action

    def test_serialization_roundtrip(self, sample_qualified_lead):
        data = sample_qualified_lead.model_dump(mode="json")
        restored = QualifiedLead.model_validate(data)
        assert restored.score == sample_qualified_lead.score
        assert restored.raw.company_name == sample_qualified_lead.raw.company_name


class TestWorkflowResult:
    def test_create(self, sample_criteria, sample_qualified_lead):
        now = datetime.now()
        result = WorkflowResult(
            run_id="abc123",
            criteria=sample_criteria,
            leads_scraped=10,
            leads_new=5,
            leads_qualified=3,
            total_input_tokens=1000,
            total_output_tokens=500,
            estimated_cost_usd=0.003,
            qualified_leads=[sample_qualified_lead],
            started_at=now,
            finished_at=now,
        )
        assert result.run_id == "abc123"
        assert len(result.qualified_leads) == 1
