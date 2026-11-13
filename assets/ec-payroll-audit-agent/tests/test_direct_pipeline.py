"""
Tests for the direct pipeline fallback (no-LLM mode):
  - _parse_month_year: natural-language month/year extraction
  - _run_pipeline_direct: end-to-end audit without LLM
"""
import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from agent import _parse_month_year, _run_pipeline_direct


# ---------------------------------------------------------------------------
# _parse_month_year tests
# ---------------------------------------------------------------------------

class TestParseMonthYear:
    def test_full_month_name(self):
        assert _parse_month_year("changes in October 2026") == (10, 2026)

    def test_abbreviated_month(self):
        assert _parse_month_year("oct 2026 report") == (10, 2026)

    def test_january_full(self):
        assert _parse_month_year("January 2025 audit") == (1, 2025)

    def test_december_abbreviated(self):
        assert _parse_month_year("dec 2024") == (12, 2024)

    def test_last_month(self):
        from datetime import date
        today = date.today()
        expected_month = today.month - 1 or 12
        expected_year = today.year if today.month > 1 else today.year - 1
        assert _parse_month_year("show last month changes") == (expected_month, expected_year)

    def test_no_month_defaults_to_today(self):
        from datetime import date
        today = date.today()
        assert _parse_month_year("show me the audit report") == (today.month, today.year)

    def test_numeric_slash_format(self):
        assert _parse_month_year("report for 10/2026") == (10, 2026)

    def test_numeric_dash_format(self):
        assert _parse_month_year("report for 10-2026") == (10, 2026)

    def test_case_insensitive(self):
        assert _parse_month_year("OCTOBER 2026") == (10, 2026)

    def test_september(self):
        assert _parse_month_year("September 2026 payroll") == (9, 2026)

    def test_november(self):
        assert _parse_month_year("November 2026 audit") == (11, 2026)


# ---------------------------------------------------------------------------
# _run_pipeline_direct tests
# ---------------------------------------------------------------------------

class TestRunPipelineDirect:
    def test_returns_string(self):
        result = _run_pipeline_direct("show EC payroll changes for October 2026")
        assert isinstance(result, str)
        assert len(result) > 100

    def test_contains_report_header(self):
        result = _run_pipeline_direct("October 2026 payroll audit")
        assert "EC Payroll Infotypes Changes Audit Report" in result
        assert "October 2026" in result

    def test_contains_executive_summary(self):
        result = _run_pipeline_direct("October 2026 changes")
        assert "Executive Summary" in result
        assert "Total Employees Affected" in result
        assert "Total Infotype Changes" in result

    def test_contains_all_three_categories(self):
        result = _run_pipeline_direct("October 2026 changes")
        assert "P2P EC-to-ECP" in result
        assert "Inbound" in result
        assert "Manual" in result

    def test_contains_before_after_columns(self):
        result = _run_pipeline_direct("October 2026 changes")
        assert "Before" in result
        assert "After" in result

    def test_direct_pipeline_note(self):
        result = _run_pipeline_direct("October 2026 changes")
        assert "direct pipeline mode" in result.lower()

    def test_november_2026(self):
        result = _run_pipeline_direct("November 2026 payroll changes")
        assert "November 2026" in result
        assert "EC Payroll Infotypes Changes Audit Report" in result

    def test_excel_export_path(self, tmp_path, monkeypatch):
        """When 'excel' keyword present, export_report is called and path returned."""
        result = _run_pipeline_direct("export October 2026 changes to excel")
        # Should return an export confirmation, not the markdown report
        assert "excel" in result.lower() or "xlsx" in result.lower() or "exported" in result.lower()

    def test_no_data_month_returns_friendly_message(self):
        """A month outside the rolling 3-month window returns a friendly no-data message."""
        result = _run_pipeline_direct("changes in January 2020")
        assert "No EC Payroll infotype changes found" in result or "January 2020" in result

    def test_last_month_resolves(self):
        """'last month' query resolves correctly without error."""
        result = _run_pipeline_direct("show me last month EC payroll changes")
        assert isinstance(result, str)
        assert len(result) > 50
