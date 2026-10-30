import re
import json
import time
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from sqlalchemy import text
from backend.database.connection import sync_engine, async_engine

# Forbidden SQL keywords to enforce read-only execution
DANGEROUS_SQL_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
]


class TTLQueryCache:
    """Thread-safe TTL in-memory query cache to reduce database load and LLM token usage."""
    def __init__(self, ttl_seconds: int = 300, max_size: int = 256):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, Tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self.ttl:
                return val
            else:
                del self._cache[key]
        return None

    def set(self, key: str, val: str):
        if len(self._cache) >= self.max_size:
            # Evict oldest entry
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[key] = (time.time(), val)

    def clear(self):
        self._cache.clear()


query_cache = TTLQueryCache(ttl_seconds=300)


def _validate_financial_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates a SQL query string against security rules.
    Returns (cleaned_query, error_message).
    """
    clean_query = query.strip()
    while clean_query.endswith(";"):
        clean_query = clean_query[:-1].strip()

    # Disallow SQL comment tokens (often used to obscure injected commands)
    if "--" in clean_query or "/*" in clean_query:
        return None, "Error: Security violation. SQL comment syntax is not permitted."

    # Disallow embedded semicolons (multi-statement execution prevention)
    if ";" in clean_query:
        return None, "Error: Security violation. Multi-statement queries are prohibited."

    # Safety checks: Must begin with SELECT, WITH, or EXPLAIN
    lower_query = clean_query.lower()
    if not (lower_query.startswith("select") or lower_query.startswith("with") or lower_query.startswith("explain")):
        return None, "Error: Security violation. Only read-only SELECT and WITH statements are permitted."

    for pattern in DANGEROUS_SQL_KEYWORDS:
        if re.search(pattern, clean_query, re.IGNORECASE):
            return None, f"Error: Security violation. Query contains unauthorized keyword: {pattern}."

    # Automatically ensure a LIMIT clause exists to guard against query exhaustion
    if "limit" not in lower_query:
        clean_query = f"{clean_query} LIMIT 50"

    return clean_query, None


def _format_sql_rows(keys: List[str], rows: List[Any]) -> str:
    if not rows:
        return "No records found matching the query."

    formatted_rows: List[Dict[str, Any]] = []
    for r in rows:
        row_dict = {}
        for k, v in zip(keys, r):
            if hasattr(v, "isoformat"):
                row_dict[k] = v.isoformat()
            elif hasattr(v, "__float__"):
                row_dict[k] = float(v)
            else:
                row_dict[k] = v
        formatted_rows.append(row_dict)

    return json.dumps(formatted_rows, indent=2)


def _sync_run_financial_query(query: str) -> str:
    """Synchronous implementation for tools/pytest."""
    clean_query, err = _validate_financial_query(query)
    if err:
        return err

    # Check analytical cache
    cached = query_cache.get(clean_query)
    if cached:
        return cached

    try:
        with sync_engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY;"))
            result = conn.execute(text(clean_query))

            if not result.returns_rows:
                return "Query executed successfully with 0 rows returned."

            keys = list(result.keys())
            rows = result.fetchmany(50)
            output = _format_sql_rows(keys, rows)
            query_cache.set(clean_query, output)
            return output
    except Exception as e:
        return f"Database Query Error: {str(e)}"


async def _async_run_financial_query(query: str) -> str:
    """Asynchronous non-blocking implementation using async_engine (asyncpg)."""
    clean_query, err = _validate_financial_query(query)
    if err:
        return err

    cached = query_cache.get(clean_query)
    if cached:
        return cached

    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SET TRANSACTION READ ONLY;"))
            result = await conn.execute(text(clean_query))

            if not result.returns_rows:
                return "Query executed successfully with 0 rows returned."

            keys = list(result.keys())
            rows = result.fetchmany(50)
            output = _format_sql_rows(keys, rows)
            query_cache.set(clean_query, output)
            return output
    except Exception as e:
        return f"Database Query Error: {str(e)}"


class FinancialQueryInput(BaseModel):
    query: str = Field(
        description="A read-only SQL SELECT statement to execute against PostgreSQL (e.g., 'SELECT category, SUM(total_amount) FROM transactions GROUP BY category;')"
    )


run_financial_query = StructuredTool.from_function(
    func=_sync_run_financial_query,
    coroutine=_async_run_financial_query,
    name="run_financial_query",
    description="""Executes a read-only SQL query against the PostgreSQL accounting database.
Available tables:
- transactions (id, date, description, vendor_id, account_id, total_amount, payment_method, category, is_reconciled, notes)
- accounts (id, code, name, type, description)
- vendors (id, name, category)
- journal_entries (id, transaction_id, account_id, debit, credit, description, entry_date)""",
    args_schema=FinancialQueryInput,
)


class ExpenseSummaryInput(BaseModel):
    start_date: Optional[str] = Field(
        default=None,
        description="Optional start date in YYYY-MM-DD format (e.g. '2025-01-01')"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Optional end date in YYYY-MM-DD format (e.g. '2025-06-30')"
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional specific expense category (e.g. 'groceries', 'utilities', 'subscriptions')"
    )
    group_by: Optional[str] = Field(
        default="category",
        description="Aggregation grouping: 'category', 'month', or 'vendor'"
    )


def _build_summary_sql(
    start_date: Optional[str],
    end_date: Optional[str],
    category: Optional[str],
    group_by: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    conditions = ["1=1"]
    params: Dict[str, Any] = {}

    if start_date:
        conditions.append("t.date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("t.date <= :end_date")
        params["end_date"] = end_date
    if category:
        conditions.append("LOWER(t.category) = LOWER(:category)")
        params["category"] = category

    where_clause = " AND ".join(conditions)

    if group_by == "month":
        sql = f"""
            SELECT 
                TO_CHAR(t.date, 'YYYY-MM') AS period,
                COUNT(t.id) AS transaction_count,
                ROUND(SUM(t.total_amount)::numeric, 2) AS total_spend,
                ROUND(AVG(t.total_amount)::numeric, 2) AS average_spend
            FROM transactions t
            WHERE {where_clause}
            GROUP BY TO_CHAR(t.date, 'YYYY-MM')
            ORDER BY period ASC;
        """
    elif group_by == "vendor":
        sql = f"""
            SELECT 
                COALESCE(v.name, 'Unknown Vendor') AS vendor_name,
                COUNT(t.id) AS transaction_count,
                ROUND(SUM(t.total_amount)::numeric, 2) AS total_spend,
                ROUND(AVG(t.total_amount)::numeric, 2) AS average_spend
            FROM transactions t
            LEFT JOIN vendors v ON t.vendor_id = v.id
            WHERE {where_clause}
            GROUP BY v.name
            ORDER BY total_spend DESC
            LIMIT 15;
        """
    else:  # default category
        sql = f"""
            SELECT 
                t.category,
                COUNT(t.id) AS transaction_count,
                ROUND(SUM(t.total_amount)::numeric, 2) AS total_spend,
                ROUND(AVG(t.total_amount)::numeric, 2) AS average_spend
            FROM transactions t
            WHERE {where_clause}
            GROUP BY t.category
            ORDER BY total_spend DESC;
        """
    return sql, params


def _format_summary_result(keys: List[str], rows: List[Any], group_by: Optional[str]) -> str:
    summary_data = []
    grand_total = 0.0
    total_count = 0

    for r in rows:
        item = {}
        for k, v in zip(keys, r):
            if hasattr(v, "__float__"):
                item[k] = float(v)
            else:
                item[k] = v
        summary_data.append(item)
        if "total_spend" in item and item["total_spend"] is not None:
            grand_total += float(item["total_spend"])
        if "transaction_count" in item and item["transaction_count"] is not None:
            total_count += int(item["transaction_count"])

    output = {
        "group_by": group_by,
        "grand_total": round(grand_total, 2),
        "total_transactions": total_count,
        "breakdown": summary_data
    }
    return json.dumps(output, indent=2)


def _sync_get_expense_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    group_by: Optional[str] = "category"
) -> str:
    cache_key = f"summary:{start_date}:{end_date}:{category}:{group_by}"
    cached = query_cache.get(cache_key)
    if cached:
        return cached

    sql, params = _build_summary_sql(start_date, end_date, category, group_by)
    try:
        with sync_engine.connect() as conn:
            result = conn.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.fetchall()
            output = _format_summary_result(keys, rows, group_by)
            query_cache.set(cache_key, output)
            return output
    except Exception as e:
        return f"Expense Summary Error: {str(e)}"


async def _async_get_expense_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    group_by: Optional[str] = "category"
) -> str:
    cache_key = f"summary:{start_date}:{end_date}:{category}:{group_by}"
    cached = query_cache.get(cache_key)
    if cached:
        return cached

    sql, params = _build_summary_sql(start_date, end_date, category, group_by)
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.fetchall()
            output = _format_summary_result(keys, rows, group_by)
            query_cache.set(cache_key, output)
            return output
    except Exception as e:
        return f"Expense Summary Error: {str(e)}"


get_expense_summary = StructuredTool.from_function(
    func=_sync_get_expense_summary,
    coroutine=_async_get_expense_summary,
    name="get_expense_summary",
    description="""Computes aggregated expense summaries including total spend, transaction count,
and average amount, grouped by category, month, or vendor.""",
    args_schema=ExpenseSummaryInput,
)
