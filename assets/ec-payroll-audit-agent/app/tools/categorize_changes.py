"""
Tool: categorize_changes
Categorizes payroll infotype changes by their source: P2P EC-to-ECP, Inbound, or Manual.
"""
import json
import logging
from typing import Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ["P2P EC-to-ECP", "Inbound", "Manual"]


@tool
def categorize_changes(changes_json: str) -> str:
    """
    Categorize a list of payroll infotype changes by their source.

    Args:
        changes_json: JSON string containing a flat list of change records
                      (output of detect_changes).

    Returns:
        JSON string containing a dict with keys:
        - "P2P EC-to-ECP": list of change records from P2P EC-to-ECP integration
        - "Inbound": list of change records from Inbound updates
        - "Manual": list of change records from Manual updates
        - "summary": dict with employee counts and change counts per category
    """
    try:
        changes = json.loads(changes_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid changes_json: {str(e)}") from e

    categorized: dict[str, list[dict[str, Any]]] = {
        "P2P EC-to-ECP": [],
        "Inbound": [],
        "Manual": [],
    }

    uncategorized = 0
    for change in changes:
        source = change.get("change_source", "")
        if source in categorized:
            categorized[source].append(change)
        else:
            uncategorized += 1

    # Build summary
    summary: dict[str, Any] = {}
    for category, records in categorized.items():
        employee_ids = {r["employee_id"] for r in records}
        summary[category] = {
            "change_count": len(records),
            "employee_count": len(employee_ids),
        }

    if uncategorized > 0:
        logger.warning(
            "M3.missed: categorization incomplete — %d records have no category assigned",
            uncategorized
        )
    else:
        p2p = summary["P2P EC-to-ECP"]["change_count"]
        inbound = summary["Inbound"]["change_count"]
        manual = summary["Manual"]["change_count"]
        logger.info(
            "M3.achieved: categorization complete — P2P:%d, Inbound:%d, Manual:%d",
            p2p, inbound, manual
        )

    result = {**categorized, "summary": summary}
    return json.dumps(result)
