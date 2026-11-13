"""Unit tests for load_employee_data tool."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from tools.load_employee_data import load_employee_data


def test_returns_100_employees():
    """Tool must return exactly 100 employees."""
    result = load_employee_data.invoke({})
    employees = json.loads(result)
    assert len(employees) == 100


def test_employees_sorted_by_salary_descending():
    """Employees must be sorted by base_salary descending."""
    result = load_employee_data.invoke({})
    employees = json.loads(result)
    salaries = [e["base_salary"] for e in employees]
    assert salaries == sorted(salaries, reverse=True)


def test_required_fields_present():
    """Each employee record must have required fields."""
    result = load_employee_data.invoke({})
    employees = json.loads(result)
    required = {"employee_id", "employee_name", "base_salary", "changes"}
    for emp in employees:
        for field in required:
            assert field in emp, f"Missing field '{field}' in employee {emp.get('employee_id')}"


def test_changes_have_required_fields():
    """Each change record must have all required fields."""
    result = load_employee_data.invoke({})
    employees = json.loads(result)
    change_fields = {
        "employee_id", "employee_name", "infotype", "field_name",
        "before_value", "after_value", "change_date", "change_source"
    }
    for emp in employees:
        for change in emp["changes"]:
            for field in change_fields:
                assert field in change, f"Missing '{field}' in change record"


def test_deterministic_output():
    """Output must be deterministic across multiple calls."""
    r1 = json.loads(load_employee_data.invoke({}))
    r2 = json.loads(load_employee_data.invoke({}))
    assert [e["employee_id"] for e in r1] == [e["employee_id"] for e in r2]
