"""
Tool: generate_report
Assembles the final EC Payroll infotypes changes audit report from categorized change data.
"""
import json
import logging
from datetime import date
from typing import Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def generate_report(categorized_json: str, target_month: Optional[int] = None, target_year: Optional[int] = None) -> str:
    """
    Assemble the final EC Payroll infotypes changes audit report from categorized change data.

    Args:
        categorized_json: JSON string output from categorize_changes tool, containing
                          categorized change records and a summary dict.
        target_month:     Calendar month number (1–12) the report covers. Defaults to current month.
        target_year:      4-digit year the report covers. Defaults to current year.

    Returns:
        A human-readable markdown string containing:
        - Executive Summary: reporting period, totals, category breakdown
        - Detailed tables per category (P2P EC-to-ECP, Inbound, Manual)
    """
    try:
        data = json.loads(categorized_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid categorized_json: {str(e)}") from e

    today = date.today()
    report_month = int(target_month) if target_month is not None else today.month
    report_year  = int(target_year)  if target_year  is not None else today.year
    import calendar as _cal
    month_name = f"{_cal.month_name[report_month]} {report_year}"
    categories = ["P2P EC-to-ECP", "Inbound", "Manual"]
    summary = data.get("summary", {})

    # Compute totals
    total_changes = sum(summary.get(c, {}).get("change_count", 0) for c in categories)
    all_employee_ids: set[str] = set()
    for c in categories:
        for record in data.get(c, []):
            all_employee_ids.add(record["employee_id"])
    total_employees = len(all_employee_ids)

    # Build Executive Summary
    lines = []
    lines.append(f"# EC Payroll Infotypes Changes Audit Report")
    lines.append(f"**Reporting Period:** {month_name}")
    lines.append(f"**Report Scope:** Top 100 highest-salaried employees")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Employees Affected | {total_employees} |")
    lines.append(f"| Total Infotype Changes | {total_changes} |")

    for cat in categories:
        cat_summary = summary.get(cat, {})
        emp_count = cat_summary.get("employee_count", 0)
        chg_count = cat_summary.get("change_count", 0)
        lines.append(f"| {cat} — Employees | {emp_count} |")
        lines.append(f"| {cat} — Changes | {chg_count} |")

    lines.append("")

    # Build Detailed Tables per category
    for cat in categories:
        records = data.get(cat, [])
        lines.append(f"## {cat} Changes ({len(records)} records)")
        lines.append("")
        if not records:
            lines.append("_No changes found for this category in the current month._")
            lines.append("")
            continue

        lines.append("| Employee ID | Employee Name | Infotype | Infotype Name | Field | Before | After | Date |")
        lines.append("|-------------|---------------|----------|---------------|-------|--------|-------|------|")
        for r in records:
            lines.append(
                f"| {r.get('employee_id','')} "
                f"| {r.get('employee_name','')} "
                f"| {r.get('infotype','')} "
                f"| {r.get('infotype_name','')} "
                f"| {r.get('field_name','')} "
                f"| {r.get('before_value','')} "
                f"| {r.get('after_value','')} "
                f"| {r.get('change_date','')} |"
            )
        lines.append("")

    report = "\n".join(lines)

    if total_changes > 0:
        logger.info(
            "M4.achieved: audit report generated — %d total changes, %d employees affected",
            total_changes, total_employees
        )
    else:
        logger.warning("M4.missed: report generation failed or exceeded time limit")

    return report
