"""Shared test fixtures."""

from __future__ import annotations

from datetime import datetime

import pytest

from first_agentic_workflow.models import QualifiedLead, RawLead, SearchCriteria


@pytest.fixture
def sample_criteria() -> SearchCriteria:
    return SearchCriteria(
        industry="SaaS",
        location="Austin, TX",
        company_size_min=10,
        company_size_max=200,
        keywords=["B2B"],
    )


@pytest.fixture
def sample_raw_lead() -> RawLead:
    return RawLead(
        company_name="Acme SaaS Inc",
        website="https://acmesaas.com",
        industry="SaaS",
        location="Austin, TX",
        employee_count=45,
        description="B2B project management platform.",
        contact_name="Jane Smith",
        contact_email="jane@acmesaas.com",
        contact_title="VP of Sales",
        source_url="https://google.com/search?q=saas+austin",
        scraped_at=datetime(2026, 1, 15, 10, 0, 0),
    )


@pytest.fixture
def sample_qualified_lead(sample_raw_lead: RawLead) -> QualifiedLead:
    return QualifiedLead(
        raw=sample_raw_lead,
        score=85,
        qualification_reasoning="Strong fit: B2B SaaS in target location and size range.",
        fit_signals=["right industry", "good size", "has contact info"],
        risk_signals=["no recent funding data"],
        recommended_action="pursue",
    )
