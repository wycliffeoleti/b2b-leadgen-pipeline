"""Tests for lead deduplication."""

import pytest

from first_agentic_workflow.dedup import Deduplicator, extract_domain, normalize_company_name
from first_agentic_workflow.models import RawLead


class TestNormalization:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Acme SaaS Inc", "acme saas"),
            ("CloudMetrics LLC", "cloudmetrics"),
            ("DataFlow Corp.", "dataflow"),
            ("TechCo Limited", "techco"),
            ("Simple", "simple"),
            ("Big Company, Inc.", "big company"),
        ],
    )
    def test_normalize_company_name(self, name, expected):
        assert normalize_company_name(name) == expected

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://www.example.com", "example.com"),
            ("https://example.com/page", "example.com"),
            ("http://www.test.io", "test.io"),
            ("example.com", "example.com"),
            (None, None),
            ("", None),
        ],
    )
    def test_extract_domain(self, url, expected):
        assert extract_domain(url) == expected


@pytest.mark.asyncio
class TestDeduplicator:
    async def test_new_lead_is_not_known(self, sample_raw_lead, tmp_path):
        dedup = Deduplicator()
        await dedup.init_db(tmp_path / "test.db")
        try:
            assert not await dedup.is_known(sample_raw_lead)
        finally:
            await dedup.close()

    async def test_marked_lead_is_known(self, sample_raw_lead, tmp_path):
        dedup = Deduplicator()
        await dedup.init_db(tmp_path / "test.db")
        try:
            await dedup.mark_seen(sample_raw_lead)
            assert await dedup.is_known(sample_raw_lead)
        finally:
            await dedup.close()

    async def test_case_insensitive_dedup(self, tmp_path):
        dedup = Deduplicator()
        await dedup.init_db(tmp_path / "test.db")
        try:
            lead1 = RawLead(
                company_name="Acme Inc",
                website="https://acme.com",
                source_url="https://google.com",
            )
            lead2 = RawLead(
                company_name="ACME INC",
                website="https://www.acme.com",
                source_url="https://google.com",
            )
            await dedup.mark_seen(lead1)
            assert await dedup.is_known(lead2)
        finally:
            await dedup.close()

    async def test_different_companies_not_deduped(self, tmp_path):
        dedup = Deduplicator()
        await dedup.init_db(tmp_path / "test.db")
        try:
            lead1 = RawLead(
                company_name="Acme", website="https://acme.com", source_url="https://google.com"
            )
            lead2 = RawLead(
                company_name="Beta", website="https://beta.com", source_url="https://google.com"
            )
            await dedup.mark_seen(lead1)
            assert not await dedup.is_known(lead2)
        finally:
            await dedup.close()

    async def test_runtime_error_without_init(self, sample_raw_lead):
        dedup = Deduplicator()
        with pytest.raises(RuntimeError, match="not initialized"):
            await dedup.is_known(sample_raw_lead)
