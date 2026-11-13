"""
Tool: load_employee_data
Loads the top 100 highest-salaried employees with their payroll infotype change records.
"""
import json
import logging
from langchain_core.tools import tool
from mock_data import get_mock_employees

logger = logging.getLogger(__name__)


@tool
def load_employee_data() -> str:
    """
    Load the top 100 highest-salaried employees with their payroll infotype change records
    for the current month from the EC Payroll mock dataset.

    Returns a JSON string containing a list of employee objects, each with:
    - employee_id: unique employee identifier
    - employee_name: full name
    - base_salary: annual base salary
    - department: department name
    - cost_center: cost center code
    - changes: list of infotype change records for the current month
    """
    try:
        employees = get_mock_employees()
        if len(employees) < 100:
            logger.warning("M1.missed: mock data generation failed or returned fewer than expected records")
        else:
            logger.info("M1.achieved: mock data loaded — 100 employees, current month change records ready")
        return json.dumps(employees)
    except Exception as e:
        logger.error("M1.missed: mock data generation failed or returned fewer than expected records")
        raise RuntimeError(f"Failed to load employee data: {str(e)}") from e
