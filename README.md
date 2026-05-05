# first-agentic-workflow

[![CI](https://github.com/wycliffeoleti/first-agentic-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/wycliffeoleti/first-agentic-workflow/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Type checked: mypy --strict](https://img.shields.io/badge/mypy-strict-blue)](http://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A small, deterministic-where-possible agentic pipeline for B2B lead generation:
**scrape → dedup → qualify (LLM) → export → notify**. AI is used for reasoning
and scoring; everything else is plain Python so errors don't compound across
chained LLM calls.

## Why this design

Each chained LLM call multiplies error probability — five 90%-accurate steps
collapse to ~59% end-to-end. So the pipeline confines AI to one step
(qualification) and uses deterministic Python for everything around it
(scraping, dedup, export, cost tracking). Three concrete consequences:

- **Dedup runs *before* the LLM**, not after — the qualifier never re-scores a
  lead, which protects the budget.
- **Hard budget cap**: the cost tracker raises `BudgetExceededError` mid-run
  rather than silently overrunning.
- **Dry-run is the default for development**: every external call has a local
  fixture path, so you can iterate at zero cost.

See [`samples/example_dry_run.csv`](samples/example_dry_run.csv) and
[`samples/example_dry_run.json`](samples/example_dry_run.json) for what a run
produces.

## What it does

The included `lead_gen` workflow takes a per-client `config.json` (industry,
location, size, keywords, qualification rules), scrapes search results via
Apify, deduplicates against a SQLite cache, qualifies the survivors with the
Gemini API, exports CSV + JSON, and posts a Slack summary if a webhook is
configured. Every external call has a `--dry-run` mode backed by local fixtures
so you can iterate without spending money.

## Install

```bash
uv sync --extra dev
cp .env.example .env
# Edit .env — at minimum set GEMINI_API_KEY for live runs.
# APIFY_TOKEN and SLACK_ALERT_WEBHOOK are optional for dry-run.
```

## Run

```bash
# Dry-run with the example client (no API calls, uses fixtures):
uv run python -m first_agentic_workflow lead_gen --dry-run --client example

# Same thing via the script entry point:
uv run python scripts/run_workflow.py lead_gen --dry-run --client example

# Live run (requires GEMINI_API_KEY and APIFY_TOKEN):
uv run python -m first_agentic_workflow lead_gen --client example
```

Outputs land in `output/<run_id>_leads.{csv,json}`. Dedup state persists in
`data/leads.db`; delete it to reset.

## Develop

```bash
uv run pytest tests/ -x -q                              # fast tests
uv run pytest tests/ -v --cov=src                       # with coverage
uv run ruff check src/ --fix && uv run ruff format src/
uv run mypy src/ --strict
```

## Adding a client

```bash
cp -r clients/example clients/<name>
# edit clients/<name>/config.json
uv run python -m first_agentic_workflow lead_gen --dry-run --client <name>
```

`clients/<name>/credentials/` is gitignored — put per-client secrets there.

## Gotcha: ROS-on-PYTHONPATH

If you have ROS 2 sourced (`/opt/ros/.../setup.bash`), it puts ROS on
`PYTHONPATH`, which leaks broken pytest plugins into this venv. Workaround:

```bash
unset PYTHONPATH
uv run pytest tests/ -x -q
```

Or run pytest in a fresh shell where ROS isn't sourced.

## Built with

Pair-programmed with [Claude Code](https://www.claude.com/product/claude-code)
(Anthropic's CLI agent). Architecture decisions, scope boundaries, design
tradeoffs, and review are mine; Claude executed code, ran the test loop, and
drafted documentation under direction. Commit history reflects this with
`Co-Authored-By:` trailers.

## License

MIT
