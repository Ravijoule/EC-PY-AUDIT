"""Integration test for ec-payroll-audit-agent end-to-end flow."""
import asyncio
import json
import sys
import os
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from tools.load_employee_data import load_employee_data
from tools.detect_changes import detect_changes
from tools.categorize_changes import categorize_changes
from tools.generate_report import generate_report


# ---------------------------------------------------------------------------
# Helper: run the full 4-tool pipeline without the LLM
# ---------------------------------------------------------------------------

def run_full_pipeline() -> str:
    """Execute the complete audit pipeline tool-by-tool (no LLM required)."""
    # Step 1 — load employees
    employees_json = load_employee_data.invoke({})
    employees = json.loads(employees_json)
    assert len(employees) == 100

    # Step 2 — detect current-month changes
    changes_json = detect_changes.invoke({"employees_json": employees_json})
    changes = json.loads(changes_json)
    # May be 0 if no mock changes fall in current month (edge case: day 1 of month)
    assert isinstance(changes, list)

    # Step 3 — categorize
    categorized_json = categorize_changes.invoke({"changes_json": changes_json})
    categorized = json.loads(categorized_json)
    assert "P2P EC-to-ECP" in categorized
    assert "Inbound" in categorized
    assert "Manual" in categorized

    # Step 4 — generate report
    report = generate_report.invoke({"categorized_json": categorized_json})
    return report


def test_pipeline_returns_report():
    """Full pipeline must produce a non-empty report string."""
    report = run_full_pipeline()
    assert isinstance(report, str)
    assert len(report) > 0


def test_report_has_executive_summary():
    """Report must contain an Executive Summary section."""
    report = run_full_pipeline()
    assert "Executive Summary" in report


def test_report_has_all_source_categories():
    """Report must contain sections for all three change sources."""
    report = run_full_pipeline()
    assert "P2P EC-to-ECP" in report
    assert "Inbound" in report
    assert "Manual" in report


def test_report_has_current_month():
    """Report must reference the current month/year."""
    report = run_full_pipeline()
    month_name = date.today().strftime("%B %Y")
    assert month_name in report


def test_report_scoped_to_top_100():
    """All employee IDs in the report must come from the top-100 dataset."""
    employees_json = load_employee_data.invoke({})
    employees = json.loads(employees_json)
    valid_ids = {e["employee_id"] for e in employees}
    assert len(valid_ids) == 100

    changes_json = detect_changes.invoke({"employees_json": employees_json})
    changes = json.loads(changes_json)
    for change in changes:
        assert change["employee_id"] in valid_ids, (
            f"Employee {change['employee_id']} is not in top-100 dataset"
        )


def test_agent_invoke_mocked_llm():
    """Agent.invoke() must succeed with mocked LLM returning the tool-generated report."""
    report = run_full_pipeline()

    # Build a fake AIMessage whose content is the real report
    from langchain_core.messages import AIMessage
    fake_ai_message = AIMessage(content=report)

    with patch("agent.ChatLiteLLM") as MockLLM, \
         patch("agent.create_checkpointer") as mock_checkpointer, \
         patch("mcp_providers.agw.get_user_sub", return_value="test-user"):

        # Set up mock LLM and graph
        mock_llm_instance = MagicMock()
        MockLLM.return_value = mock_llm_instance

        mock_checkpointer.return_value = None

        from agent import SampleAgent

        agent_instance = SampleAgent()

        # Mock the _invoke method to return messages with the report
        async def mock_invoke(*args, **kwargs):
            return {"messages": [fake_ai_message]}

        agent_instance._invoke = mock_invoke

        tools = [load_employee_data, detect_changes, categorize_changes, generate_report]

        response = asyncio.run(
            agent_instance.invoke(
                query="Generate the EC Payroll audit report for this month",
                context_id="test-context-001",
                tools=tools,
            )
        )

    assert response.status == "completed"
    assert "Executive Summary" in response.message
    assert "P2P EC-to-ECP" in response.message
    assert "Inbound" in response.message
    assert "Manual" in response.message
