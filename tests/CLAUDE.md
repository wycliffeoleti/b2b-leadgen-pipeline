# Test Commands
- Fast: `uv run pytest tests/ -x -q --tb=short`
- Full: `uv run pytest tests/ -v --cov=src`
- Skip slow: `uv run pytest tests/ -m "not slow"`
- Skip integration: `uv run pytest tests/ -m "not integration"`
