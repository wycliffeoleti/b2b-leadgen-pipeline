# first-agentic-workflow

A deterministic-where-possible agentic pipeline for B2B lead-gen: scrape → dedup → LLM-qualify → export → notify. Keeps AI confined to the reasoning step so errors don't compound.

## What — Stack & Structure
@pyproject.toml
@docs/architecture.md
@README.md

## Why — Decisions & State

**Decisions**
- **LLM = Gemini** (`google-genai`) in `processors/lead_qualifier.py`. NOTE: `docs/architecture.md` still says "default to Haiku" — that line is stale; the working code uses Gemini. Pick one when you next touch the docs.
- **Dry-run is the default development path.** Every external call (Apify, Gemini, Slack) has a `--dry-run` branch backed by local fixtures so iteration costs $0.
- **Dedup runs before the LLM**, not after. SQLite-backed (`dedup.py`) on normalized company name + domain — the LLM never re-scores a lead, which protects the budget cap.
- **Hard budget cap.** `cost_tracker.py` raises `BudgetExceededError` mid-run rather than silently overrunning. Per-workflow cap is set when the tracker is constructed.
- **Per-client isolation in `clients/<name>/`.** `config.json` holds search + qualification criteria; `credentials/` (gitignored) holds secrets. Default client is `example`.
- **Two entry points, one CLI.** `python -m first_agentic_workflow` and `scripts/run_workflow.py` both call `first_agentic_workflow.cli.main()` — keep them in sync via that function.

**State (2026-05-04)**
- Working: `lead_gen` workflow end-to-end in dry-run; 47 tests pass; ruff + mypy clean.
- Not built: any workflow other than `lead_gen`; n8n/Make JSON exports referenced in `architecture.md`; live Apify or Slack integration tests (only mocks/fixtures).
- Known gotcha: if ROS 2 is sourced, `PYTHONPATH=/opt/ros/...` leaks broken pytest plugins. `unset PYTHONPATH` before running tests, or use a fresh shell.

## How — Commands
```bash
uv sync                                    # Install deps
uv run pytest tests/ -x -q --tb=short     # Test (fast, stop on first fail)
uv run pytest tests/ -v --cov=src          # Test with coverage
uv run ruff check src/ --fix && uv run ruff format src/  # Lint + format
uv run mypy src/ --strict                               # Type check
uv run python -m first_agentic_workflow                              # Run main automation
uv run python scripts/run_workflow.py <name>         # Execute a workflow
uv run pytest tests/ -m "not integration"               # Unit tests only
```

## How — Gotchas
- Use Haiku for bulk tasks, Opus only for complex reasoning — cost discipline is margin
- Batch API gives 50% discount for async processing — use it for anything not real-time
- Enable prompt caching for repeated system prompts — up to 90% savings
- Never store client API keys in code — use `clients/{name}/credentials/` (.gitignored)
- n8n webhook URLs differ dev vs prod — use config, not hardcoded URLs
- Rate-limit external API calls with exponential backoff — respect target site limits
- Scraper selectors break when sites change — add monitoring and saved HTML snapshots

## How — Verification
- Before commits: `uv run ruff check . && uv run pytest tests/ -x -q`
- Test workflows end-to-end with sample data before client deploy
- Verify scraper selectors match target site (save HTML snapshots)
- Test connectors with sandbox/staging credentials
- Generate samples from templates before batch processing
