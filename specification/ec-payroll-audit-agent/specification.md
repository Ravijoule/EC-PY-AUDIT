# Specification: ec-payroll-audit-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` at the solution root before starting any implementation.
- [x] Bootstrap agent code in `assets/ec-payroll-audit-agent/` using instructions from the `sap-agent-bootstrap` skill. Invoke from inside `assets/ec-payroll-audit-agent/`. Use copy commands — do NOT create files manually.
- [x] Install dependencies and validate the agent starts and responds at `/.well-known/agent.json`.

---

## Runtime Skills

- [x] Create `assets/ec-payroll-audit-agent/app/skills/payroll-audit/SKILL.md` with:
  - YAML frontmatter: `name: payroll-audit`, `description: Step-by-step workflow for generating the EC Payroll infotypes changes audit report for the current month`
  - Body instructions covering:
    1. Load mock data for top 100 employees by salary
    2. Detect infotype changes within the current month with before/after values
    3. Classify each change as P2P EC-to-ECP, Inbound, or Manual
    4. Assemble the audit report (executive summary + detailed tables)
    5. Deliver the report

---

## Project-Specific Tasks

### Mock Data Layer

- [x] Create `assets/ec-payroll-audit-agent/app/mock_data.py` that generates a list of 100 employee records with:
  - Fields: `employee_id`, `employee_name`, `base_salary`, `department`, `cost_center`
  - Each employee has a list of infotype change records for the current calendar month
  - Each change record includes: `infotype`, `field_name`, `before_value`, `after_value`, `change_date` (ISO format, within current month), `change_source` (one of: `P2P EC-to-ECP`, `Inbound`, `Manual`)
  - Infotypes to cover: IT0008 (Basic Pay), IT0014 (Recurring Payments/Deductions), IT0015 (Additional Payments), IT0041 (Date Specifications), IT0006 (Address), IT0002 (Personal Data)
  - Distribute change sources realistically: ~40% P2P EC-to-ECP, ~35% Inbound, ~25% Manual
  - The dataset is deterministic (use a fixed seed) so tests produce consistent results
  - Employees are ranked by `base_salary` descending; only the top 100 are returned

### Agent Tools

- [x] Create `assets/ec-payroll-audit-agent/app/tools/load_employee_data.py`
- [x] Create `assets/ec-payroll-audit-agent/app/tools/detect_changes.py`
- [x] Create `assets/ec-payroll-audit-agent/app/tools/categorize_changes.py`
- [x] Create `assets/ec-payroll-audit-agent/app/tools/generate_report.py`

### Agent System Prompt

- [x] Update system prompt in `assets/ec-payroll-audit-agent/app/agent.py`

### Current Month Scoping

- [x] In `detect_changes.py`, implement current-month detection using Python's `datetime.now()` — compare `change_date`'s year and month against today's year and month. Do not hardcode dates.

---

## Business Instrumentation

- [x] Implement structured logging and OpenTelemetry spans for all 5 milestones (M1–M5) defined in the PRD
- [x] For `stream()` method: extracted business logic into `_run_audit()` helper with OTel span — no context manager spans inside generator
- [x] Verified `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

- [x] No `requires` entries needed in `asset.yaml` for MCP servers — the agent is self-contained with mock data
- [x] No MCP translation files or MCP server assets created
- [x] `mcp-mock-config` skill skipped (no MCP servers to mock)

---

## Testing

- [x] Write unit test `assets/ec-payroll-audit-agent/tests/test_load_employee_data.py`
- [x] Write unit test `assets/ec-payroll-audit-agent/tests/test_detect_changes.py`
- [x] Write unit test `assets/ec-payroll-audit-agent/tests/test_categorize_changes.py`
- [x] Write unit test `assets/ec-payroll-audit-agent/tests/test_generate_report.py`
- [x] Write integration test `assets/ec-payroll-audit-agent/tests/test_integration.py`
- [x] Run `pytest` from `assets/ec-payroll-audit-agent/` — 135 passed, 77% coverage (above 70% threshold)
- [x] `test_report.json` confirmed at `assets/ec-payroll-audit-agent/test_report.json`
