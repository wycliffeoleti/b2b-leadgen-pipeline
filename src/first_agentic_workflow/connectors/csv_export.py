"""Export qualified leads to CSV and JSON files."""

from __future__ import annotations

import csv
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from first_agentic_workflow.models import QualifiedLead


def _lead_to_row(lead: QualifiedLead) -> dict[str, str]:
    """Flatten a QualifiedLead into a CSV-friendly dict."""
    return {
        "company_name": lead.raw.company_name,
        "website": lead.raw.website or "",
        "industry": lead.raw.industry or "",
        "location": lead.raw.location or "",
        "employee_count": str(lead.raw.employee_count or ""),
        "contact_name": lead.raw.contact_name or "",
        "contact_email": lead.raw.contact_email or "",
        "contact_title": lead.raw.contact_title or "",
        "score": str(lead.score),
        "recommended_action": lead.recommended_action,
        "qualification_reasoning": lead.qualification_reasoning,
        "fit_signals": "; ".join(lead.fit_signals),
        "risk_signals": "; ".join(lead.risk_signals),
    }


def export_leads_csv(leads: list[QualifiedLead], output_dir: Path, run_id: str) -> Path:
    """Write qualified leads to a CSV file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run_id}_leads.csv"
    rows = [_lead_to_row(lead) for lead in leads]
    if not rows:
        path.write_text("")
        return path
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def export_leads_json(leads: list[QualifiedLead], output_dir: Path, run_id: str) -> Path:
    """Write qualified leads to a JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run_id}_leads.json"
    data = [lead.model_dump(mode="json") for lead in leads]
    path.write_text(json.dumps(data, indent=2))
    return path
