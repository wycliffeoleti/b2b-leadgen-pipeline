"""Token usage and cost tracking with budget enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field

from first_agentic_workflow.exceptions import BudgetExceededError

# Pricing per million tokens (USD)
# Gemini free tier via Google AI Studio is $0, but we track for awareness
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-flash-lite": (0.0, 0.0),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
}

_DEFAULT_PRICING = (0.10, 0.40)  # Fall back to Gemini Flash pricing


@dataclass
class CostTracker:
    """Accumulates token usage and enforces a per-run budget cap."""

    budget_usd: float
    total_input_tokens: int = field(default=0, init=False)
    total_output_tokens: int = field(default=0, init=False)
    _cost_usd: float = field(default=0.0, init=False)

    def record(self, input_tokens: int, output_tokens: int, model: str) -> None:
        """Record token usage from a single API call."""
        input_price, output_price = MODEL_PRICING.get(model, _DEFAULT_PRICING)
        cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self._cost_usd += cost
        self.check_budget()

    @property
    def total_cost_usd(self) -> float:
        """Current accumulated cost in USD."""
        return self._cost_usd

    def check_budget(self) -> None:
        """Raise BudgetExceededError if the budget cap has been exceeded."""
        if self._cost_usd > self.budget_usd:
            msg = (
                f"Budget exceeded: ${self._cost_usd:.4f} > ${self.budget_usd:.2f} "
                f"({self.total_input_tokens} input, {self.total_output_tokens} output tokens)"
            )
            raise BudgetExceededError(msg)
