"""B2B Lead Generation + Qualification workflow.

Usage:
    uv run python scripts/run_workflow.py lead_gen --dry-run
    uv run python scripts/run_workflow.py lead_gen --client example
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

import structlog

from first_agentic_workflow import config as _config
from first_agentic_workflow.connectors.csv_export import export_leads_csv, export_leads_json
from first_agentic_workflow.connectors.slack import send_slack_notification
from first_agentic_workflow.cost_tracker import CostTracker
from first_agentic_workflow.dedup import Deduplicator
from first_agentic_workflow.models import SearchCriteria, WorkflowResult
from first_agentic_workflow.processors.lead_qualifier import LeadQualifier
from first_agentic_workflow.scrapers.lead_scraper import LeadScraper

logger = structlog.get_logger()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_client_config(client: str) -> dict[str, object]:
    """Load client-specific configuration from clients/{name}/config.json."""
    config_path = _PROJECT_ROOT / "clients" / client / "config.json"
    if not config_path.exists():
        msg = f"Client config not found: {config_path}"
        raise FileNotFoundError(msg)
    return json.loads(config_path.read_text())  # type: ignore[no-any-return]


def run(*, dry_run: bool = False, client: str = "example") -> None:
    """Entry point called by run_workflow.py CLI."""
    asyncio.run(_run_async(dry_run=dry_run, client=client))


async def _run_async(*, dry_run: bool = False, client: str = "example") -> None:
    """Execute the full lead generation pipeline."""
    import logging

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if _config.settings.debug else logging.INFO,
        ),
    )
    run_id = uuid.uuid4().hex[:12]
    started_at = datetime.now()

    logger.info("workflow_start", run_id=run_id, client=client, dry_run=dry_run)

    # 1. Load client config
    client_config = _load_client_config(client)
    criteria = SearchCriteria(**client_config["search_criteria"])  # type: ignore[arg-type]
    qualification_criteria: dict[str, object] = client_config.get("qualification_criteria", {})  # type: ignore[assignment]

    # 2. Init components
    cost_tracker = CostTracker(budget_usd=_config.settings.budget_per_run_usd)
    dedup = Deduplicator()
    db_path = Path(_config.settings.db_path)
    await dedup.init_db(db_path)

    scraper = LeadScraper(apify_token=_config.settings.apify_token)
    qualifier = LeadQualifier(
        cost_tracker=cost_tracker,
        model=_config.settings.default_model,
        criteria=qualification_criteria,
        api_key=_config.settings.gemini_api_key,
        dry_run=dry_run,
    )

    try:
        # 3. Scrape
        raw_leads = await scraper.search(criteria, dry_run=dry_run)
        logger.info("scrape_complete", count=len(raw_leads))

        # 4. Dedup
        new_leads = []
        for lead in raw_leads:
            if not await dedup.is_known(lead):
                await dedup.mark_seen(lead)
                new_leads.append(lead)
        logger.info("dedup_complete", total=len(raw_leads), new=len(new_leads))

        # 5. Qualify
        qualified = await qualifier.qualify_batch(new_leads)
        logger.info("qualification_complete", qualified=len(qualified))

        # 6. Deliver
        output_dir = Path(_config.settings.output_dir)
        csv_path = export_leads_csv(qualified, output_dir, run_id)
        json_path = export_leads_json(qualified, output_dir, run_id)
        logger.info("export_complete", csv=str(csv_path), json=str(json_path))

        # 7. Build result summary
        finished_at = datetime.now()
        result = WorkflowResult(
            run_id=run_id,
            criteria=criteria,
            leads_scraped=len(raw_leads),
            leads_new=len(new_leads),
            leads_qualified=len(qualified),
            total_input_tokens=cost_tracker.total_input_tokens,
            total_output_tokens=cost_tracker.total_output_tokens,
            estimated_cost_usd=cost_tracker.total_cost_usd,
            qualified_leads=qualified,
            started_at=started_at,
            finished_at=finished_at,
        )

        # 8. Slack notification (if configured)
        if _config.settings.slack_alert_webhook and not dry_run:
            await send_slack_notification(_config.settings.slack_alert_webhook, result)

        # 9. Log summary
        logger.info(
            "workflow_complete",
            run_id=run_id,
            scraped=result.leads_scraped,
            new=result.leads_new,
            qualified=result.leads_qualified,
            cost_usd=f"${result.estimated_cost_usd:.4f}",
            duration_s=(finished_at - started_at).total_seconds(),
        )

    finally:
        await dedup.close()
