"""Tests for delivery connectors."""

import csv
import json

from first_agentic_workflow.connectors.csv_export import export_leads_csv, export_leads_json


class TestCsvExport:
    def test_export_csv(self, sample_qualified_lead, tmp_path):
        path = export_leads_csv([sample_qualified_lead], tmp_path, "test123")
        assert path.exists()
        assert path.name == "test123_leads.csv"

        with path.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["company_name"] == "Acme SaaS Inc"
        assert rows[0]["score"] == "85"
        assert rows[0]["recommended_action"] == "pursue"

    def test_export_csv_empty(self, tmp_path):
        path = export_leads_csv([], tmp_path, "empty")
        assert path.exists()
        assert path.read_text() == ""

    def test_export_json(self, sample_qualified_lead, tmp_path):
        path = export_leads_json([sample_qualified_lead], tmp_path, "test123")
        assert path.exists()
        assert path.name == "test123_leads.json"

        data = json.loads(path.read_text())
        assert len(data) == 1
        assert data[0]["raw"]["company_name"] == "Acme SaaS Inc"
        assert data[0]["score"] == 85

    def test_creates_output_dir(self, sample_qualified_lead, tmp_path):
        nested = tmp_path / "sub" / "dir"
        export_leads_csv([sample_qualified_lead], nested, "test")
        assert nested.exists()
