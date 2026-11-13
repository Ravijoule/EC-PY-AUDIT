"""
Mock data generator for EC Payroll Infotypes Audit Agent.
Generates deterministic employee records with payroll infotype changes for the current month.
"""
import random
from datetime import datetime, date, timedelta
from typing import Any

SEED = 42

FIRST_NAMES = [
    "James", "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia",
    "Benjamin", "Isabella", "Lucas", "Mia", "Henry", "Charlotte", "Alexander",
    "Amelia", "Mason", "Harper", "Ethan", "Evelyn", "Daniel", "Abigail",
    "Michael", "Emily", "Jacob", "Elizabeth", "Logan", "Sofia", "Jackson",
    "Avery", "Sebastian", "Ella", "Jack", "Scarlett", "Aiden", "Grace",
    "Owen", "Chloe", "Samuel", "Victoria", "Ryan", "Riley", "Nathan",
    "Aria", "Christian", "Lily", "David", "Aurora", "Caleb", "Zoey",
    "Elijah", "Penelope", "Jonathan", "Layla", "Carter", "Nora", "Isaiah",
    "Hannah", "Wyatt", "Lillian", "Hunter", "Addison", "Gabriel", "Eleanor",
    "Julian", "Stella", "Christopher", "Natalie", "Andrew", "Zoe", "Joshua",
    "Leah", "Charles", "Hazel", "Eli", "Violet", "Jordan", "Aurora",
    "Aaron", "Savannah", "Ian", "Audrey", "Adam", "Brooklyn", "Thomas",
    "Bella", "Evan", "Claire", "Nicholas", "Skylar", "Brayden", "Lucy",
    "Colton", "Paisley", "Diego", "Everly", "Angel", "Anna", "Roman", "Caroline"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts"
]

DEPARTMENTS = [
    "Finance", "HR", "IT", "Sales", "Marketing", "Operations",
    "Legal", "R&D", "Supply Chain", "Customer Service"
]

COST_CENTERS = [
    "CC1001", "CC1002", "CC1003", "CC1004", "CC1005",
    "CC2001", "CC2002", "CC2003", "CC3001", "CC3002"
]

INFOTYPES = {
    "IT0008": {
        "name": "Basic Pay",
        "fields": [
            ("Wage Type", ["M001-Base Salary", "M002-Base Wage"]),
            ("Amount", ["75000", "80000", "85000", "90000", "95000", "100000", "105000", "110000", "120000", "130000", "140000", "150000"]),
            ("Currency", ["USD", "EUR", "GBP"]),
            ("Pay Scale Group", ["PG01", "PG02", "PG03", "PG04", "PG05"]),
            ("Pay Scale Level", ["L01", "L02", "L03", "L04", "L05"]),
        ]
    },
    "IT0014": {
        "name": "Recurring Payments/Deductions",
        "fields": [
            ("Wage Type", ["M010-Car Allowance", "M011-Housing Allowance", "M012-Mobile Allowance"]),
            ("Amount", ["500", "750", "1000", "1200", "1500", "2000"]),
            ("Payment Method", ["Bank Transfer", "Check"]),
        ]
    },
    "IT0015": {
        "name": "Additional Payments",
        "fields": [
            ("Wage Type", ["M020-Bonus", "M021-Sign-on Bonus", "M022-Retention Bonus"]),
            ("Amount", ["5000", "7500", "10000", "12500", "15000", "20000"]),
            ("Reason", ["Performance", "Retention", "Sign-on"]),
        ]
    },
    "IT0041": {
        "name": "Date Specifications",
        "fields": [
            ("Date Type", ["01-Employment Start", "02-Seniority Date", "08-Position Start"]),
            ("Date", ["2025-01-01", "2025-03-15", "2024-07-01", "2023-01-01", "2022-06-15"]),
        ]
    },
    "IT0006": {
        "name": "Address",
        "fields": [
            ("Street", ["123 Main St", "456 Oak Ave", "789 Pine Rd", "321 Elm Dr", "654 Maple Ln"]),
            ("City", ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]),
            ("State", ["NY", "CA", "IL", "TX", "WA"]),
            ("Zip Code", ["10001", "94105", "60601", "73301", "98101"]),
        ]
    },
    "IT0002": {
        "name": "Personal Data",
        "fields": [
            ("Marital Status", ["Single", "Married", "Divorced", "Widowed"]),
            ("Tax Class", ["1", "2", "3", "4", "5", "6"]),
            ("Nationality", ["US", "UK", "DE", "FR", "CA", "AU"]),
        ]
    }
}

CHANGE_SOURCES = ["P2P EC-to-ECP", "Inbound", "Manual"]
SOURCE_WEIGHTS = [0.40, 0.35, 0.25]


def _get_rolling_window_dates(rng: random.Random) -> list[date]:
    """Generate a list of random dates spread across the last 3 calendar months
    (inclusive of the current month), so historical month queries always return data."""
    today = date.today()
    all_days: list[date] = []
    year, month = today.year, today.month
    for _ in range(3):
        d = date(year, month, 1)
        # Last day of this month
        if month == 12:
            last = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(year, month + 1, 1) - timedelta(days=1)
        # Don't go past today
        last = min(last, today)
        while d <= last:
            all_days.append(d)
            d += timedelta(days=1)
        # Step back one month
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    if not all_days:
        return [today]
    return all_days


def _generate_change_record(
    rng: random.Random,
    employee_id: str,
    employee_name: str,
    infotype: str,
    change_date: date,
) -> dict[str, Any]:
    """Generate a single infotype change record with before/after values."""
    it_config = INFOTYPES[infotype]
    field_config = rng.choice(it_config["fields"])
    field_name, values = field_config

    before_val = rng.choice(values)
    after_options = [v for v in values if v != before_val]
    if not after_options:
        after_options = values
    after_val = rng.choice(after_options)

    source = rng.choices(CHANGE_SOURCES, weights=SOURCE_WEIGHTS, k=1)[0]

    return {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "infotype": infotype,
        "infotype_name": it_config["name"],
        "field_name": field_name,
        "before_value": before_val,
        "after_value": after_val,
        "change_date": change_date.isoformat(),
        "change_source": source,
    }


def get_mock_employees() -> list[dict[str, Any]]:
    """
    Generate 100 employee records sorted by base_salary descending.
    Each employee has a list of infotype change records for the current month.
    This function is deterministic (fixed seed).
    """
    rng = random.Random(SEED)

    # Generate a larger pool and take top 100 by salary
    pool_size = 150
    employees = []
    used_names = set()

    for i in range(pool_size):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        name_key = f"{first}{last}{i}"
        while name_key in used_names:
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            name_key = f"{first}{last}{i}"
        used_names.add(name_key)

        employee_id = f"EMP{10000 + i:05d}"
        employee_name = f"{first} {last}"
        base_salary = rng.randint(60000, 350000)
        department = rng.choice(DEPARTMENTS)
        cost_center = rng.choice(COST_CENTERS)

        # Generate 3–7 change records per employee spread across the last 3 months
        available_dates = _get_rolling_window_dates(rng)
        num_changes = rng.randint(3, 7)
        infotypes_for_employee = rng.choices(list(INFOTYPES.keys()), k=num_changes)
        changes = []
        for it in infotypes_for_employee:
            change_date = rng.choice(available_dates)
            changes.append(_generate_change_record(rng, employee_id, employee_name, it, change_date))

        employees.append({
            "employee_id": employee_id,
            "employee_name": employee_name,
            "base_salary": base_salary,
            "department": department,
            "cost_center": cost_center,
            "changes": changes,
        })

    # Sort by salary descending and take top 100
    employees.sort(key=lambda e: e["base_salary"], reverse=True)
    return employees[:100]
