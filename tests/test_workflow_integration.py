"""Integration test for the lead generation workflow."""

import json

import pytest

from workflows.lead_gen import _run_async


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_dry_run(tmp_path, monkeypatch):
    """End-to-end test: scrape fixtures → dedup → qualify → export."""
    # Point DB and output to temp dirs
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "output"))

    # Reload settings with patched env
    from first_agentic_workflow import config

    monkeypatch.setattr(config, "settings", config.Settings())

    await _run_async(dry_run=True, client="example")

    # Verify output files were created
    output_dir = tmp_path / "output"
    csv_files = list(output_dir.glob("*_leads.csv"))
    json_files = list(output_dir.glob("*_leads.json"))

    assert len(csv_files) == 1
    assert len(json_files) == 1

    # Verify JSON content
    data = json.loads(json_files[0].read_text())
    assert len(data) == 5  # All fixture leads (first run = no dupes)
    assert all(d["score"] == 50 for d in data)  # Dry-run scores
