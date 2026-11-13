"""Unit tests for detect_changes tool."""
import json
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from tools.detect_changes import detect_changes


def _make_employees(changes):
    return json.dumps([{
        "employee_id": "EMP10001",
        "employee_name": "Test User",
        "base_salary": 100000,
        "changes": changes,
    }])


def _current_month_date() -> str:
    today = date.today()
    return date(today.year, today.month, 5).isoformat()


def _previous_month_date() -> str:
    today = date.today()
    first = date(today.year, today.month, 1)
    prev = first - timedelta(days=1)
    return prev.isoformat()


def _make_change(change_date: str, source: str = "Manual") -> dict:
    return {
        "employee_id": "EMP10001",
        "employee_name": "Test User",
        "infotype": "IT0008",
        "infotype_name": "Basic Pay",
        "field_name": "Amount",
        "before_value": "80000",
        "after_value": "85000",
        "change_date": change_date,
        "change_source": source,
    }


def test_current_month_change_included():
    """Changes within the current month must be returned."""
    employees = _make_employees([_make_change(_current_month_date())])
    result = json.loads(detect_changes.invoke({"employees_json": employees}))
    assert len(result) == 1


def test_previous_month_change_excluded():
    """Changes from a previous month must not be returned."""
    employees = _make_employees([_make_change(_previous_month_date())])
    result = json.loads(detect_changes.invoke({"employees_json": employees}))
    assert len(result) == 0


def test_mixed_months_only_current_returned():
    """Only current-month changes are returned when both months present."""
    employees = _make_employees([
        _make_change(_current_month_date()),
        _make_change(_previous_month_date()),
    ])
    result = json.loads(detect_changes.invoke({"employees_json": employees}))
    assert len(result) == 1


def test_returned_record_has_required_fields():
    """Each returned change must have all required fields."""
    employees = _make_employees([_make_change(_current_month_date())])
    result = json.loads(detect_changes.invoke({"employees_json": employees}))
    required = {"employee_id", "employee_name", "infotype", "field_name",
                "before_value", "after_value", "change_date", "change_source"}
    for record in result:
        for field in required:
            assert field in record


def test_empty_employees_returns_empty():
    """Empty employee list returns empty changes."""
    result = json.loads(detect_changes.invoke({"employees_json": json.dumps([])}))
    assert result == []


def test_change_source_preserved():
    """The change_source field must be preserved accurately."""
    employees = _make_employees([_make_change(_current_month_date(), source="P2P EC-to-ECP")])
    result = json.loads(detect_changes.invoke({"employees_json": employees}))
    assert result[0]["change_source"] == "P2P EC-to-ECP"
