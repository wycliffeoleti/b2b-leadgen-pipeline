# first-agentic-workflow

A small, deterministic-where-possible agentic pipeline for B2B lead generation:
**scrape → dedup → qualify (LLM) → export → notify**. AI is used for reasoning
and scoring; everything else is plain Python so errors don't compound across
chained LLM calls.

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

## License

MIT
