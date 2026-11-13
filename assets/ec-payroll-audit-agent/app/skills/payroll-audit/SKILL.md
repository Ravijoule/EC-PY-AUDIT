---
name: payroll-audit
description: Step-by-step workflow for generating the EC Payroll infotypes changes audit report for the current month, covering change detection, categorization by source, and report assembly with before/after values.
---

# EC Payroll Infotypes Audit Workflow

## When to Use This Skill

Load this skill when the user requests any of the following:
- An EC Payroll audit report
- Infotype changes for the current month
- Payroll change categorization (P2P / Inbound / Manual)
- Before/after values for payroll field changes

## Prerequisite

Confirm the request is scoped to the **current calendar month** and the **top 100 highest-salaried employees**. If the user requests a different period or scope, note the limitation and proceed with the default scope.

## Instructions

### Step 1: Load Employee Data

Call the `load_employee_data` tool.
- This returns a JSON list of the top 100 employees by base salary.
- Each employee record includes change records for the current month.
- Do not proceed if this step fails — surface the error to the user.

### Step 2: Detect Current-Month Changes

Call the `detect_changes` tool with the JSON output from Step 1.
- This filters all infotype changes to only those within the current calendar month.
- Each change record includes: employee_id, employee_name, infotype, field_name, before_value, after_value, change_date, change_source.
- If the result is empty, inform the user that no changes were found for the current month and stop.

### Step 3: Categorize Changes by Source

Call the `categorize_changes` tool with the JSON output from Step 2.
- This classifies each change into one of three categories:
  - **P2P EC-to-ECP**: changes propagated via the P2P integration between Employee Central and EC Payroll
  - **Inbound**: changes received from external inbound feeds
  - **Manual**: changes entered directly by HR or payroll administrators

The output includes a summary dict with employee counts and change counts per category.

### Step 4: Generate the Audit Report

Call the `generate_report` tool with the JSON output from Step 3.
- This assembles the full markdown audit report including:
  - **Executive Summary**: reporting period, total employees affected, total changes, breakdown by category
  - **Detailed Tables**: one table per category showing Employee ID, Employee Name, Infotype, Infotype Name, Field, Before Value, After Value, Change Date

### Step 5: Deliver the Report

Return the complete markdown report to the user exactly as returned by `generate_report`.
- Do not summarize or truncate the report.
- If the report is large, deliver it in full — the user needs all records for audit purposes.

## Error Handling

| Error Condition | Action |
|-----------------|--------|
| `load_employee_data` fails | Report the error verbatim. Do not proceed. |
| `detect_changes` returns empty list | Inform user: "No infotype changes found for the current month." |
| `categorize_changes` reports uncategorized records | Include a note in your response about uncategorized records. |
| `generate_report` fails | Report the error verbatim. |

## Example Interaction

**User:** "Generate the payroll audit report for this month."

**Expected Flow:**
1. Call `load_employee_data` → receive 100 employee records
2. Call `detect_changes` with employee data → receive filtered change list
3. Call `categorize_changes` with changes → receive categorized dict + summary
4. Call `generate_report` with categorized data → receive formatted markdown report
5. Return report to user
