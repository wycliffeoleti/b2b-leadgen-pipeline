"""Domain models for lead generation workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SearchCriteria(BaseModel):
    """Criteria for searching and filtering potential leads."""

    industry: str
    location: str
    company_size_min: int = 1
    company_size_max: int = 10000
    keywords: list[str] = Field(default_factory=list)


class RawLead(BaseModel):
    """Unqualified lead data extracted from scraping."""

    company_name: str
    website: str | None = None
    industry: str | None = None
    location: str | None = None
    employee_count: int | None = None
    description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_title: str | None = None
    source_url: str
    scraped_at: datetime = Field(default_factory=datetime.now)


class QualifiedLead(BaseModel):
    """Lead with AI-generated qualification scoring."""

    raw: RawLead
    score: int = Field(ge=0, le=100)
    qualification_reasoning: str
    fit_signals: list[str] = Field(default_factory=list)
    risk_signals: list[str] = Field(default_factory=list)
    recommended_action: Literal["pursue", "nurture", "skip"]


class WorkflowResult(BaseModel):
    """Summary of a complete lead generation workflow run."""

    run_id: str
    criteria: SearchCriteria
    leads_scraped: int
    leads_new: int
    leads_qualified: int
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    qualified_leads: list[QualifiedLead]
    started_at: datetime
    finished_at: datetime
