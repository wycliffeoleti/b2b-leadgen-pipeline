"""Tests for lead scraper."""

import pytest

from first_agentic_workflow.models import SearchCriteria
from first_agentic_workflow.scrapers.lead_scraper import LeadScraper, _build_search_query


class TestBuildSearchQuery:
    def test_basic_query(self):
        criteria = SearchCriteria(industry="SaaS", location="Austin, TX")
        query = _build_search_query(criteria)
        assert "SaaS" in query
        assert "Austin, TX" in query

    def test_with_size_range(self):
        criteria = SearchCriteria(
            industry="SaaS", location="Austin", company_size_min=10, company_size_max=200
        )
        query = _build_search_query(criteria)
        assert "10-200 employees" in query

    def test_with_keywords(self):
        criteria = SearchCriteria(industry="SaaS", location="Austin", keywords=["B2B", "startup"])
        query = _build_search_query(criteria)
        assert "B2B" in query
        assert "startup" in query


class TestLeadScraperDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_returns_fixtures(self, sample_criteria):
        scraper = LeadScraper()
        leads = await scraper.search(sample_criteria, dry_run=True)
        assert len(leads) == 5
        assert leads[0].company_name == "Acme SaaS Inc"

    @pytest.mark.asyncio
    async def test_live_requires_token(self, sample_criteria):
        scraper = LeadScraper(apify_token="")
        with pytest.raises(ValueError, match="Apify token required"):
            await scraper.search(sample_criteria, dry_run=False)
