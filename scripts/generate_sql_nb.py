import json

def create_sql_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 🗄️ SQL SDET MASTERY NOTEBOOK (40 PROGRESSIVE EXERCISES)\n",
                    "**Target**: York Solutions / Optum SDET Interview Preparation\n",
                    "**Candidate**: Lokender Singh\n",
                    "**Kernel**: Python (ai-expense-venv)\n",
                    "\n",
                    "### Database Architecture Available:\n",
                    "1. **`optum_healthcare_db` (Port 5432)**: Healthcare claims, patients, providers, appointments, audit logs (Exercises 1-15)\n",
                    "2. **`chaicode_ecom_db` (Port 5432)**: Customers, orders, order items, products, employees (Exercises 16-28)\n",
                    "3. **`expense_accounting_db` (Port 5433)**: General ledger, accounts, double-entry vouchers (Exercises 29-40)\n",
                    "\n",
                    "---"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Database Helper Functions\n",
                    "import pandas as pd\n",
                    "from sqlalchemy import create_engine\n",
                    "\n",
                    "# Engine 1: Healthcare DB (Port 5432)\n",
                    "engine_health = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/optum_healthcare_db')\n",
                    "# Engine 2: Ecom DB (Port 5432)\n",
                    "engine_ecom = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/chaicode_ecom_db')\n",
                    "# Engine 3: Accounting DB (Port 5433)\n",
                    "engine_acct = create_engine('postgresql+psycopg2://postgres:postgrespassword@localhost:5433/expense_accounting_db')\n",
                    "\n",
                    "def run_sql(query: str, db='health') -> pd.DataFrame:\n",
                    "    engine = engine_health if db == 'health' else (engine_ecom if db == 'ecom' else engine_acct)\n",
                    "    return pd.read_sql_query(query, engine)\n",
                    "\n",
                    "print('Database connection helper initialized!')"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python (ai-expense-venv)",
                "language": "python",
                "name": "ai-expense-venv"
            },
            "language_info": {
                "name": "python",
                "version": "3.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    exercises = [
        # Part 1: optum_healthcare_db (Exercises 1-15)
        ("Exercise 1: Total Claims Billed vs Approved by Status",
         "Query `claims` table. Group by `claim_status`. Return status, total claims count, total billed amount, and total approved amount. Sort descending by total billed amount.",
         "health",
         "query_1 = \"\"\"\n-- YOUR SQL QUERY HERE\nSELECT \n    claim_status,\n    COUNT(*) AS total_claims,\n    SUM(billed_amount) AS total_billed,\n    SUM(approved_amount) AS total_approved\nFROM claims\nGROUP BY claim_status\nORDER BY total_billed DESC;\n\"\"\"\nrun_sql(query_1, 'health')"),

        ("Exercise 2: Finding Denied Claims with Patient Details",
         "Join `claims` and `patients`. Select `claim_id`, `patient_name` (combine first_name and last_name), `state`, `diagnosis_code`, and `billed_amount` for all claims where `claim_status = 'DENIED'` and `billed_amount > 1000`.",
         "health",
         "query_2 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_2, 'health')"),

        ("Exercise 3: Top 3 Highest Earning Providers by Specialty (Window DENSE_RANK)",
         "Join `claims` and `providers`. Calculate total approved revenue for each provider. Use `DENSE_RANK() OVER (PARTITION BY specialty ORDER BY total_approved DESC)` to find the top provider in each specialty.",
         "health",
         "query_3 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_3, 'health')"),

        ("Exercise 4: Detecting Duplicate Claim Submissions (SDET Consistency Check)",
         "Find potential duplicate claims: claims with the same `patient_id`, `provider_id`, `diagnosis_code`, `procedure_code`, and `submission_date` that occur more than once.",
         "health",
         "query_4 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_4, 'health')"),

        ("Exercise 5: Average Adjudication Turnaround Time (Date Math)",
         "Calculate the average number of days taken to adjudicate claims (`adjudication_date - submission_date`) grouped by `claim_status` for all resolved claims (`PAID` or `DENIED`).",
         "health",
         "query_5 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_5, 'health')"),

        ("Exercise 6: Finding Patients with Appointments but Zero Claims (LEFT JOIN / Orphan Check)",
         "Identify patients who have at least one appointment in `appointments`, but have never submitted any claims in `claims`.",
         "health",
         "query_6 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_6, 'health')"),

        ("Exercise 7: Running Cumulative Total of Approved Claims Over Time",
         "Using Window function `SUM(...) OVER (ORDER BY submission_date)`, calculate a day-by-day cumulative total of approved claims for 2026.",
         "health",
         "query_7 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_7, 'health')"),

        ("Exercise 8: Claims Approval Ratio by Diagnosis Code (CASE WHEN)",
         "For each `diagnosis_code`, calculate: total claims, total paid claims, and approval percentage: `ROUND(100.0 * SUM(CASE WHEN claim_status = 'PAID' THEN 1 ELSE 0 END) / COUNT(*), 2)`. Filter for diagnosis codes with at least 5 claims.",
         "health",
         "query_8 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_8, 'health')"),

        ("Exercise 9: Second Highest Billed Claim in Each Specialty",
         "Find the 2nd highest billed claim for each provider `specialty`. Return `specialty`, `provider_name`, `claim_id`, and `billed_amount`.",
         "health",
         "query_9 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_9, 'health')"),

        ("Exercise 10: Most Frequently Prescribed Medications per Provider",
         "Query `prescriptions`. Find the top medication prescribed by each provider using `ROW_NUMBER() OVER (PARTITION BY provider_id ORDER BY COUNT(*) DESC)`.",
         "health",
         "query_10 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_10, 'health')"),

        ("Exercise 11: Patients with No-Show Appointments and Outstanding Balances",
         "Find patients who had a `NO_SHOW` appointment status and also have claims currently in `PENDING` or `IN_REVIEW` status.",
         "health",
         "query_11 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_11, 'health')"),

        ("Exercise 12: Month-over-Month Claim Volume Growth (LAG Window Function)",
         "Aggregate claim count by month (extract month from `submission_date`). Use `LAG()` to show current month claims, previous month claims, and the difference.",
         "health",
         "query_12 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_12, 'health')"),

        ("Exercise 13: Finding Outlier Claims (> 2x Provider Specialty Average)",
         "Identify any claim whose `billed_amount` is greater than 2 times the average billed amount for that provider's `specialty`.",
         "health",
         "query_13 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_13, 'health')"),

        ("Exercise 14: Audit Trail Reconciliation (Tracking Status Changes)",
         "Join `claims` with `claim_audit_logs`. Verify if the current `claims.claim_status` matches the `new_status` of the most recent audit log entry for that claim.",
         "health",
         "query_14 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_14, 'health')"),

        ("Exercise 15: Patients with Refills Expiring Soon",
         "Find all patients with active prescriptions where `refills_remaining = 0` and the prescription was written in the last 60 days.",
         "health",
         "query_15 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_15, 'health')"),

        # Part 2: chaicode_ecom_db (Exercises 16-28)
        ("Exercise 16: Total Revenue per Product Category",
         "Join `categories`, `products`, and `order_items` in `chaicode_ecom_db`. Return category name and total sales revenue.",
         "ecom",
         "query_16 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_16, 'ecom')"),

        ("Exercise 17: Customers with Zero Orders (LEFT JOIN Anti-Pattern)",
         "Find customers who have never placed an order in `chaicode_ecom_db`.",
         "ecom",
         "query_17 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_17, 'ecom')"),

        ("Exercise 18: Employee Salary Ranking by Department",
         "Query `employees` and `departments`. Use `DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC)` to rank employees.",
         "ecom",
         "query_18 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_18, 'ecom')"),

        ("Exercise 19: Finding Employees Earning More than Department Average (Correlated Subquery)",
         "Find employees whose salary is strictly greater than the average salary of their own department.",
         "ecom",
         "query_19 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_19, 'ecom')"),

        ("Exercise 20: Self-Join (Employees and Their Managers)",
         "Display employee name and their direct manager's name from `employees` table.",
         "ecom",
         "query_20 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_20, 'ecom')"),

        ("Exercise 21: Top 2 Highest Spending Customers (CTE)",
         "Using a CTE, find total spend per customer and rank them to select the top 2.",
         "ecom",
         "query_21 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_21, 'ecom')"),

        ("Exercise 22: Order Status Distribution (Pivoting with CASE WHEN)",
         "Pivot orders table into count of pending, shipped, and delivered orders.",
         "ecom",
         "query_22 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_22, 'ecom')"),

        ("Exercise 23: Mismatched Payment vs Order Amounts",
         "Join `orders` and `payments` to find orders where `payments.amount != orders.total_amount`.",
         "ecom",
         "query_23 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_23, 'ecom')"),

        ("Exercise 24: Products Ordered in All Categories (Relational Division)",
         "Find customers who have purchased products from more than 2 distinct categories.",
         "ecom",
         "query_24 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_24, 'ecom')"),

        ("Exercise 25: First and Last Order per Customer (FIRST_VALUE / LAST_VALUE)",
         "Extract the date of the first order and most recent order for every customer.",
         "ecom",
         "query_25 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_25, 'ecom')"),

        ("Exercise 26: Moving Average of Order Values (Window Frames)",
         "Calculate a 3-order moving average of order totals sorted by order_date.",
         "ecom",
         "query_26 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_26, 'ecom')"),

        ("Exercise 27: Recursive Hierarchy (Org Tree)",
         "Use a `RECURSIVE CTE` to traverse from top executive down to all direct and indirect reportees.",
         "ecom",
         "query_27 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_27, 'ecom')"),

        ("Exercise 28: UNION vs UNION ALL Performance Comparison",
         "Combine active and archived orders, explaining difference between UNION (deduplicating sort) and UNION ALL.",
         "ecom",
         "query_28 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_28, 'ecom')"),

        # Part 3: expense_accounting_db (Exercises 29-40)
        ("Exercise 29: Double-Entry Ledger Zero-Sum Verification",
         "Assert that total debits equal total credits across all journal lines in `expense_accounting_db`.",
         "acct",
         "query_29 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_29, 'acct')"),

        ("Exercise 30: Unbalanced Journal Vouchers Detection",
         "Find any transaction voucher where `SUM(debit) != SUM(credit)`.",
         "acct",
         "query_30 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_30, 'acct')"),

        ("Exercise 31: Account Category Spend Breakdown",
         "Group journal entry lines by top-level account head (Asset, Liability, Equity, Revenue, Expense).",
         "acct",
         "query_31 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_31, 'acct')"),

        ("Exercise 32: Finding Orphaned Journal Lines",
         "Find journal lines that do not link to any valid transaction header record.",
         "acct",
         "query_32 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_32, 'acct')"),

        ("Exercise 33: Auditing Unauthorized Modifications via Timestamps",
         "Compare transaction creation timestamps against audit log timestamps to detect backdated entries.",
         "acct",
         "query_33 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_33, 'acct')"),

        ("Exercise 34: Cumulative Cash Burn Rate (Window Frame)",
         "Calculate cumulative cash outflows day-by-day for the fiscal year.",
         "acct",
         "query_34 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_34, 'acct')"),

        ("Exercise 35: Reconciled vs Pending Expense Ratio",
         "Calculate the percentage of total transactions marked as reconciled.",
         "acct",
         "query_35 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_35, 'acct')"),

        ("Exercise 36: Simulating Pessimistic Locking (SELECT FOR UPDATE)",
         "Write a transaction block query demonstrating `SELECT ... FOR UPDATE` to lock a record during reconciliation.",
         "acct",
         "query_36 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_36, 'acct')"),

        ("Exercise 37: Query Execution Plan Analysis (EXPLAIN ANALYZE)",
         "Run `EXPLAIN ANALYZE` on a complex join query across transactions and accounts to inspect index scans vs sequential scans.",
         "acct",
         "query_37 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_37, 'acct')"),

        ("Exercise 38: Index Optimization Impact Check",
         "Demonstrate query execution cost before and after adding a composite B-Tree index.",
         "acct",
         "query_38 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_38, 'acct')"),

        ("Exercise 39: Finding Missing Sequential Invoice / Voucher Numbers",
         "Identify any gaps in sequential voucher numbering (e.g., missing voucher #104 between #103 and #105).",
         "acct",
         "query_39 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_39, 'acct')"),

        ("Exercise 40: Master Consistency Quality Gate Query",
         "Create a single master query returning a summary table of 5 integrity checks: (Debits=Credits, No Orphans, Zero Duplicates, Reconciled %, Audit Coverage).",
         "acct",
         "query_40 = \"\"\"\n-- YOUR SQL QUERY HERE\n\"\"\"\nrun_sql(query_40, 'acct')")
    ]

    for title, desc, db, stub in exercises:
        nb["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"### {title}\n", f"**Database**: `{db}` | **Requirement**: {desc}\n"]
        })
        nb["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [stub]
        })

    with open("notebooks/02_sql_sdet_mastery.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print("Created notebooks/02_sql_sdet_mastery.ipynb with 40 exercises!")

if __name__ == "__main__":
    create_sql_notebook()

