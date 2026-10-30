# 🗄️ SQL SDET CONCEPTUAL GUIDE
**Target**: Understanding Core Relational Database Concepts & Window Functions for SDET Technical Interviews  
*Note: This document explains the underlying mechanics, execution lifecycle, join behaviors, and window function mathematics. No direct exercise solutions are given so you can solve them in `notebooks/02_sql_sdet_mastery.ipynb`.*

---

## 1. The Real Execution Order of a SQL Query

Most engineers read SQL in written order (`SELECT` $\rightarrow$ `FROM` $\rightarrow$ `WHERE`). The database engine executes in a completely different order:

| Step | Clause | What the Database Engine Does |
| :--- | :--- | :--- |
| **1** | **`FROM` & `JOIN`** | Identifies source tables and performs Cartesian/Join operations to assemble the working rowset. |
| **2** | **`WHERE`** | Filters raw rows based on row-level predicates before any grouping happens. |
| **3** | **`GROUP BY`** | Collapses the filtered rows into distinct summary buckets. |
| **4** | **`HAVING`** | Filters the aggregated buckets using aggregate conditions (`COUNT(*) > 1`). |
| **5** | **`SELECT`** | Evaluates column expressions, computes math, and applies aliases. |
| **6** | **`DISTINCT`** | Eliminates duplicate output rows. |
| **7** | **`WINDOW`** | Evaluates window functions (`OVER (PARTITION BY ...)`). |
| **8** | **`ORDER BY`** | Sorts the final output rows. |
| **9** | **`LIMIT` / `OFFSET`** | Restricts the total number of emitted rows. |

> [!IMPORTANT]
> **Why Aliases Fail in `WHERE` Clauses**:
> In an interview, if you write `SELECT amount * 1.18 AS total ... WHERE total > 100`, it fails with `column "total" does not exist`. Why? Because `WHERE` (Step 2) executes before `SELECT` (Step 5) creates the alias! You must repeat the expression in `WHERE` or wrap it in a CTE.

---

## 2. Aggregations, GROUP BY & HAVING

### `WHERE` vs `HAVING`
- **`WHERE`**: Operates on individual rows before aggregation occurs. Cannot contain aggregate functions (`WHERE SUM(amount) > 500` is illegal).
- **`HAVING`**: Operates on the grouped buckets produced by `GROUP BY`. Filters based on aggregate calculations (`HAVING COUNT(*) > 1` or `HAVING SUM(amount) > 50000`).

### `COUNT(*)` vs `COUNT(column)`
- `COUNT(*)`: Counts every single row in the bucket, including rows where some columns are `NULL`.
- `COUNT(column)`: Counts only rows where the specified `column` is strictly **NOT NULL**.

### `COALESCE(val1, val2, ...)`
Evaluates arguments from left to right and returns the first non-NULL value.
- **SDET Pattern**: Handling NULL balances, commissions, or approval amounts: `COALESCE(approved_amount, 0.00)`.

---

## 3. Multi-Table JOINs & Integrity Checking

### `INNER JOIN`
Returns only rows that satisfy the join condition in **both** tables. If a patient has no claims, they are excluded entirely.

### `LEFT JOIN` (and Anti-Join Orphan Detection)
Returns all rows from the left table, and matching rows from the right table. If no match exists, all right-table columns become `NULL`.
- **The SDET Anti-Join Pattern (Finding Orphan Records / Churn)**:
  How do you find patients who registered but never visited a doctor, or customers who never placed an order?
  ```sql
  SELECT p.patient_id, p.first_name, p.last_name
  FROM patients p
  LEFT JOIN appointments a ON p.patient_id = a.patient_id
  WHERE a.appointment_id IS NULL;
  ```
  If `a.appointment_id IS NULL` after a `LEFT JOIN`, the patient has zero matching appointments!

### Self-Join
Joining a table to itself using two different aliases.
- **Classic Interview Scenario**: Employees and Managers. The `employees` table contains `manager_id` referencing `employee_id` in the same table:
  ```sql
  SELECT e.emp_name AS employee, m.emp_name AS manager
  FROM employees e
  LEFT JOIN employees m ON e.manager_id = m.employee_id;
  ```

---

## 4. Window Functions: The Analytics Engine

### Concept: Window Function vs `GROUP BY`
- `GROUP BY` **collapses** multiple rows into a single summary row. Individual row identity is lost.
- A **Window Function** performs calculations across a set of table rows that are related to the current row, but **does NOT collapse the rows**. Every single input row remains present in the output.

### Anatomy of an `OVER (...)` Clause
```sql
FUNCTION() OVER (
    PARTITION BY category 
    ORDER BY total_amount DESC
    ROWS BETWEEN ...
)
```
- **`PARTITION BY`**: Divides the rows into separate groups (like mini-tables). The function evaluates independently inside each partition.
- **`ORDER BY`**: Defines the evaluation sequence of rows inside each partition.

### The Big Three Ranking Functions
Suppose transaction amounts in a category are: `[500, 500, 300, 100]`.

| Function | Output for `[500, 500, 300, 100]` | Behavior on Ties | Subsequent Numbers |
| :--- | :--- | :--- | :--- |
| **`ROW_NUMBER()`** | `1, 2, 3, 4` | Assigns arbitrary sequential integers. Never ties. | Strictly consecutive. |
| **`RANK()`** | `1, 1, 3, 4` | Assigns identical rank to ties. | **Skips ranks** (skips 2 because two rows tied for 1). |
| **`DENSE_RANK()`** | `1, 1, 2, 3` | Assigns identical rank to ties. | **Never skips ranks** (next distinct value gets 2). |

> [!TIP]
> **Finding Nth Highest (e.g. 2nd Highest Salary or Claim)**:
> Always use `DENSE_RANK()` inside a CTE or subquery:
> ```sql
> WITH ranked_claims AS (
>     SELECT 
>         specialty, claim_id, billed_amount,
>         DENSE_RANK() OVER (PARTITION BY specialty ORDER BY billed_amount DESC) as rnk
>     FROM claims
> )
> SELECT * FROM ranked_claims WHERE rnk = 2;
> ```

### `LEAD()` and `LAG()` (Time-Series & Growth Calculations)
- **`LAG(column, offset, default)`**: Accesses data from a previous row at a specified physical offset within the partition.
  - *SDET Use Case*: Month-over-month growth: `current_month_sales - LAG(monthly_sales, 1) OVER (ORDER BY month)`.
- **`LEAD(column, offset, default)`**: Accesses data from a subsequent row ahead of the current row.

### Cumulative Running Totals & Window Frames
When you write `SUM(amount) OVER (ORDER BY date)`, PostgreSQL defaults the window frame to:
`RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
- This accumulates all rows from the beginning of the partition up to the current row.
- **Moving Average (e.g. 7-Day Window)**:
  `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` restricts the calculation to exactly the past 6 rows plus the current row.

---

## 5. Subqueries, CTEs & Duplicate Detection

### Correlated Subqueries
A correlated subquery is a subquery that refers to a column from the outer query. It evaluates once for every single row evaluated by the outer query:
```sql
SELECT e1.emp_name, e1.salary, e1.dept_id
FROM employees e1
WHERE e1.salary > (
    SELECT AVG(e2.salary) 
    FROM employees e2 
    WHERE e2.dept_id = e1.dept_id
);
```

### Common Table Expressions (`WITH ... AS (...)`)
A CTE defines a temporary named result set available only during the execution of the main statement.
- **Advantages**: Dramatically more readable than nested subqueries; can be referenced multiple times; supports `RECURSIVE` CTEs for hierarchical organizational trees.

### Duplicate Record Detection
To find duplicate records in a table:
```sql
SELECT patient_id, provider_id, diagnosis_code, submission_date, COUNT(*)
FROM claims
GROUP BY patient_id, provider_id, diagnosis_code, submission_date
HAVING COUNT(*) > 1;
```

---

## 6. Data Integrity & Financial Ledger Rules

### Double-Entry Accounting Invariant
In double-entry financial engines (like our `expense_accounting_db`):
- Every journal voucher must be balanced: $\sum \text{Debits} - \sum \text{Credits} = 0$.
- **The SDET Consistency Assertion**:
  ```sql
  SELECT SUM(debit) - SUM(credit) AS net_imbalance FROM journal_lines;
  ```
  If `net_imbalance != 0.00`, data corruption has occurred.

### Concurrency & Pessimistic Locking (`SELECT ... FOR UPDATE`)
When multiple concurrent requests attempt to book the same appointment slot or approve the same claim voucher, race conditions occur.
- `SELECT ... FOR UPDATE` locks the selected rows against concurrent transactions until the current transaction commits or rolls back, preventing double-booking anomalies.

### `EXPLAIN ANALYZE` (Execution Plan Inspection)
Tells you how the query planner actually executes your SQL:
- **`Seq Scan`**: Scanned every row in the table sequentially. Slow for large tables.
- **`Index Scan`**: Traversed a B-tree index to locate specific pointers, then fetched data from the heap.
- **`Index Only Scan`**: All requested columns existed directly in the index; table heap was never touched (fastest).
- **`Cost`**: Unitless planner estimate `(cost=startup..total)`.
- **`Actual time`**: Real wall-clock execution time in milliseconds.

