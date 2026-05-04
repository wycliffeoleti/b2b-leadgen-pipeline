"""Slack webhook notifications for workflow results."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import structlog

if TYPE_CHECKING:
    from first_agentic_workflow.models import WorkflowResult

logger = structlog.get_logger()


def _format_message(result: WorkflowResult) -> dict[str, object]:
    """Format a WorkflowResult as a Slack message payload."""
    pursue = [ql for ql in result.qualified_leads if ql.recommended_action == "pursue"]
    nurture = [ql for ql in result.qualified_leads if ql.recommended_action == "nurture"]

    lines = [
        f"*Lead Gen Run Complete* (`{result.run_id}`)",
        f"Industry: {result.criteria.industry} | Location: {result.criteria.location}",
        f"Scraped: {result.leads_scraped} | New: {result.leads_new}",
        f"Qualified: {result.leads_qualified}",
        f"Pursue: {len(pursue)} | Nurture: {len(nurture)}",
        f"Cost: ${result.estimated_cost_usd:.4f}",
    ]

    if pursue:
        lines.append("\n*Top Leads to Pursue:*")
        for lead in pursue[:5]:
            lines.append(f"  - {lead.raw.company_name} (score: {lead.score})")

    return {"text": "\n".join(lines)}


async def send_slack_notification(webhook_url: str, result: WorkflowResult) -> None:
    """POST workflow results to a Slack webhook."""
    payload = _format_message(result)
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
    logger.info("slack_notification_sent", run_id=result.run_id)
