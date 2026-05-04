# Architecture

## Why This Structure
Deterministic tools prevent compound error — if each AI step is 90% accurate, five chained steps drop to 59%. Offload execution to deterministic scripts; keep AI for reasoning and orchestration only. Check `src/first_agentic_workflow/` for existing tools before building new ones.

## Directory Layout
- `workflows/` — n8n/Make JSON exports and workflow documentation
- `src/first_agentic_workflow/scrapers/` — Apify actors and custom scraping logic
- `src/first_agentic_workflow/processors/` — AI processing (Claude API calls, data transforms)
- `src/first_agentic_workflow/connectors/` — Integrations (Slack, email, CRM, webhooks)
- `src/first_agentic_workflow/templates/` — Jinja2 prompt templates for content generation
- `clients/` — Per-client configs, credentials (.gitignored), and deliverables
- `scripts/` — CLI entry points for running workflows

## Data Flow
```
Trigger → Dedup → Scrape → Process (Claude API) → Deliver → Track Cost
```

## Conventions
- Default to Haiku for all Claude API calls
- Enable prompt caching for repeated system prompts
- Each client gets isolated config in `clients/{name}/`
- Budget caps enforced per workflow run
- Use `/retrospective` after work sessions to feed improvements back into config
