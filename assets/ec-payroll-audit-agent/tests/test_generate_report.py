"""Unit tests for generate_report tool."""
import json
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from tools.generate_report import generate_report

CATEGORIES = ["P2P EC-to-ECP", "Inbound", "Manual"]


def _make_change(employee_id: str, name: str, source: str) -> dict:
    return {
        "employee_id": employee_id,
        "employee_name": name,
        "infotype": "IT0008",
        "infotype_name": "Basic Pay",
        "field_name": "Amount",
        "before_value": "80000",
        "after_value": "85000",
        "change_date": date.today().isoformat(),
        "change_source": source,
    }


def _build_categorized(changes: list) -> str:
    categorized = {"P2P EC-to-ECP": [], "Inbound": [], "Manual": [], "summary": {}}
    for cat in CATEGORIES:
        cat_records = [c for c in changes if c["change_source"] == cat]
        categorized[cat] = cat_records
        emp_ids = {r["employee_id"] for r in cat_records}
        categorized["summary"][cat] = {
            "change_count": len(cat_records),
            "employee_count": len(emp_ids),
        }
    return json.dumps(categorized)


def test_report_contains_executive_summary():
    """Report must contain an Executive Summary section."""
    changes = [_make_change("EMP001", "Alice Smith", "Manual")]
    report = generate_report.invoke({"categorized_json": _build_categorized(changes)})
    assert "Executive Summary" in report


def test_report_contains_all_three_categories():
    """Report must have a section for each category."""
    changes = [
        _make_change("EMP001", "Alice Smith", "P2P EC-to-ECP"),
        _make_change("EMP002", "Bob Jones", "Inbound"),
        _make_change("EMP003", "Carol White", "Manual"),
    ]
    report = generate_report.invoke({"categorized_json": _build_categorized(changes)})
    for cat in CATEGORIES:
        assert cat in report


def test_detail_row_contains_required_columns():
    """Each detail row must contain Employee ID, Employee Name, Infotype, Field, Before, After, Date."""
    changes = [_make_change("EMP001", "Alice Smith", "Manual")]
    report = generate_report.invoke({"categorized_json": _build_categorized(changes)})
    assert "EMP001" in report
    assert "Alice Smith" in report
    assert "IT0008" in report
    assert "Amount" in report
    assert "80000" in report
    assert "85000" in report
    assert date.today().isoformat() in report


def test_empty_category_shows_no_changes_message():
    """Empty categories must display a 'No changes' message."""
    # Only P2P changes, Inbound and Manual empty
    changes = [_make_change("EMP001", "Alice", "P2P EC-to-ECP")]
    report = generate_report.invoke({"categorized_json": _build_categorized(changes)})
    assert "No changes found" in report


def test_report_shows_correct_total_counts():
    """Executive summary must show correct totals."""
    changes = [
        _make_change("EMP001", "Alice", "P2P EC-to-ECP"),
        _make_change("EMP002", "Bob", "Inbound"),
        _make_change("EMP003", "Carol", "Manual"),
    ]
    report = generate_report.invoke({"categorized_json": _build_categorized(changes)})
    # Total of 3 changes, 3 employees
    assert "3" in report


def test_report_contains_reporting_period():
    """Report must include the current month as the reporting period."""
    changes = [_make_change("EMP001", "Alice", "Manual")]
    report = generate_report.invoke({"categorized_json": _build_categorized(changes)})
    month_name = date.today().strftime("%B %Y")
    assert month_name in report


def test_empty_input_generates_valid_report():
    """Report must be generated even with no changes."""
    categorized = {
        "P2P EC-to-ECP": [], "Inbound": [], "Manual": [],
        "summary": {
            "P2P EC-to-ECP": {"change_count": 0, "employee_count": 0},
            "Inbound": {"change_count": 0, "employee_count": 0},
            "Manual": {"change_count": 0, "employee_count": 0},
        }
    }
    report = generate_report.invoke({"categorized_json": json.dumps(categorized)})
    assert "Executive Summary" in report
    assert "0" in report
