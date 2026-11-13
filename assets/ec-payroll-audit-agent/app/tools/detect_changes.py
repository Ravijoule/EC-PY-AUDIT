"""
Tool: detect_changes
Filters payroll infotype change records to only those within a specified calendar month.
Defaults to the current month when no month/year is provided.
"""
import json
import logging
from datetime import date
from typing import Any, Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def detect_changes(employees_json: str, target_month: Optional[int] = None, target_year: Optional[int] = None) -> str:
    """
    Given a JSON string of employee records (output of load_employee_data), returns all
    infotype field changes that fall within the specified calendar month with before/after values.

    Args:
        employees_json: JSON string containing a list of employee records with their changes.
        target_month:   Calendar month number (1–12). Defaults to current month if omitted.
        target_year:    4-digit year (e.g. 2026). Defaults to current year if omitted.

    Returns:
        JSON string containing a flat list of change records within the target month, each with:
        - employee_id, employee_name, infotype, infotype_name, field_name,
          before_value, after_value, change_date, change_source
    """
    try:
        employees = json.loads(employees_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid employees_json: {str(e)}") from e

    today = date.today()
    filter_year  = int(target_year)  if target_year  is not None else today.year
    filter_month = int(target_month) if target_month is not None else today.month

    if not 1 <= filter_month <= 12:
        raise ValueError(f"target_month must be 1–12, got {filter_month}")
    if filter_year < 2000 or filter_year > 2100:
        raise ValueError(f"target_year must be between 2000 and 2100, got {filter_year}")

    filtered: list[dict[str, Any]] = []

    for emp in employees:
        for change in emp.get("changes", []):
            try:
                change_date = date.fromisoformat(change["change_date"])
            except (ValueError, KeyError):
                continue
            if change_date.year == filter_year and change_date.month == filter_month:
                filtered.append({
                    "employee_id":    change["employee_id"],
                    "employee_name":  change["employee_name"],
                    "infotype":       change["infotype"],
                    "infotype_name":  change.get("infotype_name", ""),
                    "field_name":     change["field_name"],
                    "before_value":   change["before_value"],
                    "after_value":    change["after_value"],
                    "change_date":    change["change_date"],
                    "change_source":  change["change_source"],
                })

    total = len(filtered)
    unique_employees = len({c["employee_id"] for c in filtered})

    import calendar
    month_label = f"{calendar.month_name[filter_month]} {filter_year}"

    if total == 0:
        logger.warning(
            "M2.missed: no change records found for %s", month_label
        )
    else:
        logger.info(
            "M2.achieved: change detection complete — %d changes across %d employees for %s",
            total, unique_employees, month_label
        )

    return json.dumps(filtered)
