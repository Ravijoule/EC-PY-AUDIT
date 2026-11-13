"""Unit tests for categorize_changes tool."""
import json
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from tools.categorize_changes import categorize_changes

CATEGORIES = ["P2P EC-to-ECP", "Inbound", "Manual"]


def _make_change(employee_id: str, source: str) -> dict:
    return {
        "employee_id": employee_id,
        "employee_name": f"Employee {employee_id}",
        "infotype": "IT0008",
        "infotype_name": "Basic Pay",
        "field_name": "Amount",
        "before_value": "80000",
        "after_value": "85000",
        "change_date": date.today().isoformat(),
        "change_source": source,
    }


def _invoke(changes: list) -> dict:
    return json.loads(categorize_changes.invoke({"changes_json": json.dumps(changes)}))


def test_output_has_all_category_keys():
    """Output must contain all three category keys."""
    result = _invoke([_make_change("EMP001", "Manual")])
    for cat in CATEGORIES:
        assert cat in result


def test_summary_key_present():
    """Output must include a 'summary' dict."""
    result = _invoke([_make_change("EMP001", "Manual")])
    assert "summary" in result


def test_p2p_change_categorized_correctly():
    """P2P EC-to-ECP changes go to the correct bucket."""
    result = _invoke([_make_change("EMP001", "P2P EC-to-ECP")])
    assert len(result["P2P EC-to-ECP"]) == 1
    assert len(result["Inbound"]) == 0
    assert len(result["Manual"]) == 0


def test_inbound_change_categorized_correctly():
    """Inbound changes go to the correct bucket."""
    result = _invoke([_make_change("EMP001", "Inbound")])
    assert len(result["Inbound"]) == 1
    assert len(result["P2P EC-to-ECP"]) == 0
    assert len(result["Manual"]) == 0


def test_manual_change_categorized_correctly():
    """Manual changes go to the correct bucket."""
    result = _invoke([_make_change("EMP001", "Manual")])
    assert len(result["Manual"]) == 1


def test_each_change_in_exactly_one_category():
    """Each change record must appear in exactly one category."""
    changes = [
        _make_change("EMP001", "P2P EC-to-ECP"),
        _make_change("EMP002", "Inbound"),
        _make_change("EMP003", "Manual"),
    ]
    result = _invoke(changes)
    total_in_categories = sum(len(result[c]) for c in CATEGORIES)
    assert total_in_categories == len(changes)


def test_summary_employee_count():
    """Summary must report correct distinct employee counts per category."""
    changes = [
        _make_change("EMP001", "Manual"),
        _make_change("EMP001", "Manual"),  # same employee, 2 changes
        _make_change("EMP002", "Manual"),
    ]
    result = _invoke(changes)
    assert result["summary"]["Manual"]["employee_count"] == 2
    assert result["summary"]["Manual"]["change_count"] == 3


def test_summary_change_count():
    """Summary change_count must equal total records per category."""
    changes = [
        _make_change("EMP001", "P2P EC-to-ECP"),
        _make_change("EMP002", "P2P EC-to-ECP"),
        _make_change("EMP003", "Inbound"),
    ]
    result = _invoke(changes)
    assert result["summary"]["P2P EC-to-ECP"]["change_count"] == 2
    assert result["summary"]["Inbound"]["change_count"] == 1
    assert result["summary"]["Manual"]["change_count"] == 0


def test_empty_input_returns_empty_categories():
    """Empty input returns empty lists for all categories."""
    result = _invoke([])
    for cat in CATEGORIES:
        assert result[cat] == []
