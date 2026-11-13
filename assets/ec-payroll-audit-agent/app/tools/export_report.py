"""
Tool: export_report
Exports the EC Payroll infotypes changes audit report to an Excel workbook (.xlsx).
Produces four sheets: Summary, P2P EC-to-ECP, Inbound, Manual.
"""
import calendar
import json
import logging
import os
from datetime import date
from typing import Optional

import openpyxl
from openpyxl.styles import (
    Alignment, Border, Font, PatternFill, Side
)
from openpyxl.utils import get_column_letter
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ── Colour palette ──────────────────────────────────────────────────────────
_HEADER_FILLS = {
    "Summary":        PatternFill("solid", fgColor="1F4E79"),   # dark blue
    "P2P EC-to-ECP":  PatternFill("solid", fgColor="2E75B6"),   # blue
    "Inbound":        PatternFill("solid", fgColor="375623"),    # dark green
    "Manual":         PatternFill("solid", fgColor="7B2C2C"),    # dark red
}
_TITLE_FILL   = PatternFill("solid", fgColor="D6E4F0")          # light blue title bar
_ALT_FILL     = PatternFill("solid", fgColor="EAF4FB")           # alternating row tint
_WHITE_FILL   = PatternFill("solid", fgColor="FFFFFF")
_THIN_BORDER  = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"),  bottom=Side(style="thin"),
)
_WHITE_FONT   = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
_BOLD_FONT    = Font(name="Calibri", bold=True, size=11)
_BODY_FONT    = Font(name="Calibri", size=10)
_TITLE_FONT   = Font(name="Calibri", bold=True, size=13, color="1F4E79")


def _write_header_row(ws, row: int, cols: list[str], fill: PatternFill) -> None:
    for c, label in enumerate(cols, start=1):
        cell = ws.cell(row=row, column=c, value=label)
        cell.font      = _WHITE_FONT
        cell.fill      = fill
        cell.border    = _THIN_BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _write_data_row(ws, row: int, values: list, shade: bool) -> None:
    fill = _ALT_FILL if shade else _WHITE_FILL
    for c, val in enumerate(values, start=1):
        cell = ws.cell(row=row, column=c, value=val)
        cell.font      = _BODY_FONT
        cell.fill      = fill
        cell.border    = _THIN_BORDER
        cell.alignment = Alignment(vertical="center", wrap_text=True)


def _auto_width(ws, min_w: int = 10, max_w: int = 45) -> None:
    for col_cells in ws.columns:
        length = max(
            len(str(cell.value)) if cell.value is not None else 0
            for cell in col_cells
        )
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = (
            min(max(length + 2, min_w), max_w)
        )


def _write_change_sheet(
    wb: openpyxl.Workbook,
    sheet_name: str,
    records: list[dict],
    month_label: str,
) -> None:
    ws = wb.create_sheet(title=sheet_name)
    fill = _HEADER_FILLS[sheet_name]

    # Title row
    ws.merge_cells("A1:J1")
    title_cell = ws["A1"]
    title_cell.value     = f"EC Payroll Audit — {sheet_name} Changes — {month_label}"
    title_cell.font      = _TITLE_FONT
    title_cell.fill      = _TITLE_FILL
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 24

    cols = [
        "#", "Employee ID", "Employee Name", "Infotype",
        "Infotype Name", "Field", "Before Value", "After Value",
        "Change Date", "Change Source",
    ]
    _write_header_row(ws, 2, cols, fill)
    ws.row_dimensions[2].height = 20

    for i, rec in enumerate(records, start=1):
        row_idx = i + 2
        _write_data_row(ws, row_idx, [
            i,
            rec.get("employee_id", ""),
            rec.get("employee_name", ""),
            rec.get("infotype", ""),
            rec.get("infotype_name", ""),
            rec.get("field_name", ""),
            rec.get("before_value", ""),
            rec.get("after_value", ""),
            rec.get("change_date", ""),
            rec.get("change_source", ""),
        ], shade=(i % 2 == 0))

    _auto_width(ws)
    ws.freeze_panes = "A3"


def _write_summary_sheet(
    wb: openpyxl.Workbook,
    summary: dict,
    month_label: str,
    total_employees: int,
    total_changes: int,
) -> None:
    ws = wb.create_sheet(title="Summary", index=0)
    fill = _HEADER_FILLS["Summary"]

    # Main title
    ws.merge_cells("A1:D1")
    t = ws["A1"]
    t.value     = f"EC Payroll Infotypes Changes Audit Report — {month_label}"
    t.font      = Font(name="Calibri", bold=True, size=14, color="1F4E79")
    t.fill      = _TITLE_FILL
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:D2")
    s = ws["A2"]
    s.value     = "Scope: Top 100 highest-salaried employees"
    s.font      = Font(name="Calibri", italic=True, size=10, color="595959")
    s.alignment = Alignment(horizontal="center")
    ws.row_dimensions[2].height = 16

    # Section header
    _write_header_row(ws, 4, ["Category", "Employees Affected", "Total Changes", "% of All Changes"], fill)
    ws.row_dimensions[4].height = 20

    categories = ["P2P EC-to-ECP", "Inbound", "Manual"]
    rows = [
        ("Overall Total", total_employees, total_changes, "100%"),
    ]
    for cat in categories:
        cat_data = summary.get(cat, {})
        emp_c  = cat_data.get("employee_count", 0)
        chg_c  = cat_data.get("change_count", 0)
        pct    = f"{round(chg_c / total_changes * 100, 1)}%" if total_changes else "0%"
        rows.append((cat, emp_c, chg_c, pct))

    for i, row_data in enumerate(rows, start=5):
        shade = (i % 2 == 0)
        _write_data_row(ws, i, list(row_data), shade)
        # bold the "Overall Total" row
        if i == 5:
            for c in range(1, 5):
                ws.cell(row=i, column=c).font = _BOLD_FONT

    # Infotype breakdown header
    ws.cell(row=10, column=1).value = "Infotype Breakdown"
    ws.cell(row=10, column=1).font  = _BOLD_FONT

    _write_header_row(ws, 11, ["Infotype", "Infotype Name", "Changes", "% of All Changes"], fill)

    _auto_width(ws)
    ws.freeze_panes = "A5"


@tool
def export_report(
    categorized_json: str,
    target_month: Optional[int] = None,
    target_year: Optional[int] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Export the EC Payroll infotypes changes audit report to a formatted Excel workbook.

    Creates a multi-sheet .xlsx file with:
    - Summary sheet: executive totals and infotype breakdown
    - P2P EC-to-ECP sheet: all P2P changes with before/after values
    - Inbound sheet: all Inbound changes with before/after values
    - Manual sheet: all Manual changes with before/after values

    Args:
        categorized_json: JSON string output from categorize_changes tool.
        target_month:     Month number (1–12) the report covers. Defaults to current month.
        target_year:      4-digit year the report covers. Defaults to current year.
        output_path:      File path for the .xlsx output. Defaults to
                          /tmp/ec_payroll_audit_<month>_<year>.xlsx

    Returns:
        The absolute path of the generated Excel file.
    """
    try:
        data = json.loads(categorized_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid categorized_json: {str(e)}") from e

    today       = date.today()
    rpt_month   = int(target_month) if target_month is not None else today.month
    rpt_year    = int(target_year)  if target_year  is not None else today.year
    month_label = f"{calendar.month_name[rpt_month]} {rpt_year}"

    categories  = ["P2P EC-to-ECP", "Inbound", "Manual"]
    summary     = data.get("summary", {})

    # Totals
    total_changes   = sum(summary.get(c, {}).get("change_count", 0) for c in categories)
    all_emp_ids: set[str] = set()
    for cat in categories:
        for rec in data.get(cat, []):
            all_emp_ids.add(rec["employee_id"])
    total_employees = len(all_emp_ids)

    # Default output path
    if not output_path:
        output_path = f"/tmp/ec_payroll_audit_{calendar.month_abbr[rpt_month].lower()}_{rpt_year}.xlsx"

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # 1. Summary sheet
    _write_summary_sheet(wb, summary, month_label, total_employees, total_changes)

    # Fill in infotype breakdown on summary sheet
    ws_sum = wb["Summary"]
    all_records = [rec for cat in categories for rec in data.get(cat, [])]
    infotype_counts: dict[str, dict] = {}
    for rec in all_records:
        it = rec.get("infotype", "")
        it_name = rec.get("infotype_name", "")
        if it not in infotype_counts:
            infotype_counts[it] = {"name": it_name, "count": 0}
        infotype_counts[it]["count"] += 1

    for i, (it_code, it_data) in enumerate(sorted(infotype_counts.items()), start=12):
        pct = f"{round(it_data['count'] / total_changes * 100, 1)}%" if total_changes else "0%"
        _write_data_row(ws_sum, i, [it_code, it_data["name"], it_data["count"], pct], shade=(i % 2 == 0))

    # 2–4. One sheet per category
    for cat in categories:
        _write_change_sheet(wb, cat, data.get(cat, []), month_label)

    wb.save(output_path)
    abs_path = os.path.abspath(output_path)
    logger.info(
        "Excel export complete — %d changes, %d employees → %s",
        total_changes, total_employees, abs_path,
    )
    return abs_path
