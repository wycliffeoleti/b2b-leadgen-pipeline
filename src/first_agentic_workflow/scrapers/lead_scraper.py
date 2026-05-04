"""Lead scraping via Apify actors with dry-run fixture support."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from first_agentic_workflow.models import RawLead, SearchCriteria

logger = structlog.get_logger()

# Default Apify actor IDs (configurable)
DEFAULT_SEARCH_ACTOR = "apify/google-search-scraper"
DEFAULT_WEB_ACTOR = "apify/website-content-crawler"


def _build_search_query(criteria: SearchCriteria) -> str:
    """Build a Google search query from criteria."""
    parts = [f"{criteria.industry} companies in {criteria.location}"]
    if criteria.company_size_min > 1 or criteria.company_size_max < 10000:
        parts.append(f"{criteria.company_size_min}-{criteria.company_size_max} employees")
    parts.extend(criteria.keywords)
    return " ".join(parts)


def _fixture_leads() -> list[RawLead]:
    """Return sample leads for dry-run testing."""
    now = datetime.now()
    return [
        RawLead(
            company_name="Acme SaaS Inc",
            website="https://acmesaas.com",
            industry="SaaS",
            location="Austin, TX",
            employee_count=45,
            description="B2B project management platform for mid-market teams.",
            contact_name="Jane Smith",
            contact_email="jane@acmesaas.com",
            contact_title="VP of Sales",
            source_url="https://google.com/search?q=saas+austin",
            scraped_at=now,
        ),
        RawLead(
            company_name="CloudMetrics LLC",
            website="https://cloudmetrics.io",
            industry="SaaS",
            location="Austin, TX",
            employee_count=120,
            description="Cloud infrastructure monitoring and observability platform.",
            contact_name="Bob Johnson",
            contact_email="bob@cloudmetrics.io",
            contact_title="CTO",
            source_url="https://google.com/search?q=saas+austin",
            scraped_at=now,
        ),
        RawLead(
            company_name="DataFlow Corp",
            website="https://dataflow.dev",
            industry="Developer Tools",
            location="Austin, TX",
            employee_count=30,
            description="ETL pipeline builder for data engineering teams.",
            contact_name=None,
            contact_email=None,
            contact_title=None,
            source_url="https://google.com/search?q=saas+austin",
            scraped_at=now,
        ),
        RawLead(
            company_name="TinyStartup",
            website="https://tinystartup.io",
            industry="SaaS",
            location="Austin, TX",
            employee_count=3,
            description="Pre-revenue MVP for social media scheduling.",
            contact_name="Alex Lee",
            contact_email="alex@tinystartup.io",
            contact_title="Founder",
            source_url="https://google.com/search?q=saas+austin",
            scraped_at=now,
        ),
        RawLead(
            company_name="GovSecure Ltd",
            website="https://govsecure.com",
            industry="Cybersecurity",
            location="Austin, TX",
            employee_count=500,
            description="Enterprise security solutions for government and defense.",
            contact_name="Sarah Williams",
            contact_email="sarah@govsecure.com",
            contact_title="Director of BD",
            source_url="https://google.com/search?q=saas+austin",
            scraped_at=now,
        ),
    ]


class LeadScraper:
    """Scrape potential leads using Apify actors."""

    def __init__(
        self,
        apify_token: str = "",
        search_actor: str = DEFAULT_SEARCH_ACTOR,
        web_actor: str = DEFAULT_WEB_ACTOR,
    ) -> None:
        self._apify_token = apify_token
        self._search_actor = search_actor
        self._web_actor = web_actor

    async def search(
        self,
        criteria: SearchCriteria,
        *,
        dry_run: bool = False,
        max_results: int = 20,
    ) -> list[RawLead]:
        """Search for leads matching criteria."""
        if dry_run:
            logger.info("scraper_dry_run", criteria=criteria.model_dump())
            return _fixture_leads()

        if not self._apify_token:
            msg = "Apify token required for live scraping. Set APIFY_TOKEN in .env."
            raise ValueError(msg)

        query = _build_search_query(criteria)
        logger.info("scraping_leads", query=query, max_results=max_results)

        raw_results = await self._run_search_actor(query, max_results)
        return self._parse_results(raw_results)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    async def _run_search_actor(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Run Apify Google Search actor with retry."""
        from apify_client import ApifyClientAsync

        client = ApifyClientAsync(token=self._apify_token)
        run_input = {
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": max_results,
        }
        run = await client.actor(self._search_actor).call(run_input=run_input)
        if run is None:
            return []
        dataset = client.dataset(run["defaultDatasetId"])
        items: list[dict[str, Any]] = []
        async for item in dataset.iterate_items():
            items.append(item)  # type: ignore[arg-type, unused-ignore]
        return items

    @staticmethod
    def _parse_results(results: list[dict[str, Any]]) -> list[RawLead]:
        """Parse Apify Google Search actor results into RawLead models."""
        leads: list[RawLead] = []
        now = datetime.now()
        for item in results:
            # Google Search actor nests results under organicResults
            organic = item.get("organicResults", [])
            if organic:
                for result in organic:
                    url = result.get("url", "")
                    if not url:
                        continue
                    leads.append(
                        RawLead(
                            company_name=result.get("title", "Unknown"),
                            website=url,
                            description=result.get("description"),
                            source_url=url,
                            scraped_at=now,
                        )
                    )
            else:
                # Fallback for flat result format
                url = item.get("url", "")
                if not url:
                    continue
                leads.append(
                    RawLead(
                        company_name=item.get("title", "Unknown"),
                        website=url,
                        description=item.get("description"),
                        source_url=url,
                        scraped_at=now,
                    )
                )
        return leads
