"""AI-powered lead qualification using Google Gemini API."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import structlog
from google import genai
from google.genai.errors import ClientError
from jinja2 import Environment, FileSystemLoader

from first_agentic_workflow.cost_tracker import CostTracker  # noqa: TCH001
from first_agentic_workflow.models import QualifiedLead, RawLead  # noqa: TCH001

logger = structlog.get_logger()

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_JSON_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```|(\{[\s\S]*\})")

_MAX_RETRIES = 3


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from an LLM response, handling markdown code blocks."""
    match = _JSON_RE.search(text)
    if match:
        raw = match.group(1) or match.group(2)
        return json.loads(raw)  # type: ignore[no-any-return]
    return json.loads(text)  # type: ignore[no-any-return]


class LeadQualifier:
    """Qualifies leads by scoring them with Gemini Flash."""

    def __init__(
        self,
        cost_tracker: CostTracker,
        model: str = "gemini-2.0-flash",
        criteria: dict[str, Any] | None = None,
        *,
        api_key: str = "",
        dry_run: bool = False,
    ) -> None:
        self._cost_tracker = cost_tracker
        self._model = model
        self._criteria = criteria or {}
        self._dry_run = dry_run
        self._api_key = api_key
        self._client: genai.Client | None = None
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=True,
        )

    async def _call_gemini(self, prompt: str) -> genai.types.GenerateContentResponse:
        """Call Gemini API with retry on rate limits."""
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key or None)

        for attempt in range(_MAX_RETRIES):
            try:
                return await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
            except ClientError as exc:
                if exc.code == 429 and attempt < _MAX_RETRIES - 1:
                    wait = 2 ** (attempt + 1) * 15  # 30s, 60s
                    logger.warning(
                        "rate_limited",
                        attempt=attempt + 1,
                        wait_seconds=wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise
        msg = "Unreachable"
        raise RuntimeError(msg)  # pragma: no cover

    async def qualify(self, lead: RawLead) -> QualifiedLead:
        """Score and qualify a single lead."""
        if self._dry_run:
            return self._dummy_result(lead)

        template = self._jinja_env.get_template("lead_qualification.j2")
        prompt = template.render(lead=lead, criteria=self._criteria)

        response = await self._call_gemini(prompt)

        # Track token usage
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count or 0 if usage else 0
        output_tokens = usage.candidates_token_count or 0 if usage else 0
        self._cost_tracker.record(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
        )

        text = response.text or ""
        parsed = _extract_json(text)

        return QualifiedLead(
            raw=lead,
            score=parsed["score"],
            qualification_reasoning=parsed["qualification_reasoning"],
            fit_signals=parsed.get("fit_signals", []),
            risk_signals=parsed.get("risk_signals", []),
            recommended_action=parsed["recommended_action"],
        )

    async def qualify_batch(self, leads: list[RawLead]) -> list[QualifiedLead]:
        """Qualify leads sequentially for predictable budget tracking."""
        results: list[QualifiedLead] = []
        for i, lead in enumerate(leads):
            logger.info(
                "qualifying_lead",
                company=lead.company_name,
                progress=f"{i + 1}/{len(leads)}",
            )
            result = await self.qualify(lead)
            results.append(result)
        return results

    @staticmethod
    def _dummy_result(lead: RawLead) -> QualifiedLead:
        """Return a placeholder result for dry-run mode."""
        return QualifiedLead(
            raw=lead,
            score=50,
            qualification_reasoning="Dry run — no API call made.",
            fit_signals=["dry_run"],
            risk_signals=[],
            recommended_action="nurture",
        )
