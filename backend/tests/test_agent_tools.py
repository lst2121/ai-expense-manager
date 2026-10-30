import json
import pytest
from backend.agent.tools.sql_analytics import run_financial_query, get_expense_summary
from backend.agent.tools.chart_tool import generate_chart_spec
from backend.agent.tools.temporal_tool import get_current_datetime
from backend.agent.tools.web_search_tool import web_search


def test_sql_query_valid_read_only():
    """Verify safe SELECT queries return parsed JSON records."""
    raw_res = run_financial_query.invoke({"query": "SELECT category, COUNT(*) as count FROM transactions GROUP BY category ORDER BY count DESC LIMIT 3;"})
    data = json.loads(raw_res)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "category" in data[0]
    assert "count" in data[0]


def test_sql_query_blocks_dangerous_operations():
    """Verify security guards block mutating operations."""
    destructive_queries = [
        "DROP TABLE transactions;",
        "DELETE FROM transactions WHERE id = 1;",
        "UPDATE transactions SET total_amount = 9999;",
        "TRUNCATE TABLE journal_entries;",
        "ALTER TABLE accounts ADD COLUMN fake_col text;",
        "CREATE TABLE hack (id int);",
    ]

    for bad_sql in destructive_queries:
        res = run_financial_query.invoke({"query": bad_sql})
        assert "Security violation" in res or "Error" in res, f"Expected security error for query: {bad_sql}"


def test_get_expense_summary_by_category():
    """Verify aggregated summary by category."""
    raw_res = get_expense_summary.invoke({"group_by": "category"})
    summary = json.loads(raw_res)

    assert "grand_total" in summary
    assert summary["grand_total"] > 100000.0  # From sample data (~116k)
    assert "breakdown" in summary
    assert len(summary["breakdown"]) >= 5

    categories = [b["category"].lower() for b in summary["breakdown"]]
    assert "subscriptions" in categories or "rent" in categories


def test_get_expense_summary_by_month():
    """Verify aggregated summary grouped by month."""
    raw_res = get_expense_summary.invoke({"group_by": "month"})
    summary = json.loads(raw_res)

    assert summary["group_by"] == "month"
    assert len(summary["breakdown"]) > 0
    first_period = summary["breakdown"][0]
    assert "period" in first_period
    assert "total_spend" in first_period


def test_generate_chart_spec():
    """Verify structured chart spec generation for Recharts."""
    sample_data = [
        {"category": "Rent", "amount": 5000.0},
        {"category": "Subscriptions", "amount": 1200.0},
    ]

    raw_res = generate_chart_spec.invoke({
        "chart_type": "bar",
        "title": "Top Spending Categories",
        "x_key": "category",
        "y_keys": ["amount"],
        "data": sample_data,
        "description": "Breakdown of major expenses"
    })

    spec = json.loads(raw_res)
    assert spec.get("__chart__") is True
    assert spec.get("chart_type") == "bar"
    assert spec.get("title") == "Top Spending Categories"
    assert spec.get("x_key") == "category"
    assert spec.get("y_keys") == ["amount"]
    assert len(spec.get("data", [])) == 2


def test_temporal_tool_current_datetime():
    """Verify temporal anchor returns current date, time, weekday, and fiscal quarter."""
    res = get_current_datetime.invoke({"timezone_str": "Asia/Kolkata"})
    assert "Current Date:" in res
    assert "Day of Week:" in res
    assert "Current Quarter: Q" in res
    assert "ISO 8601:" in res


def test_web_search_tool():
    """Verify web search tool executes cleanly with structured output."""
    res = web_search.invoke({"query": "India inflation rate", "max_results": 2})
    assert isinstance(res, str)
    assert len(res) > 0
    # Should either have title/summary or graceful note
    assert "Title:" in res or "No web search results" in res or "error" not in res.lower()


def test_sql_query_blocks_multistatement_injection():
    """Verify semicolon injection is blocked."""
    res = run_financial_query.invoke({"query": "SELECT 1; SELECT 2;"})
    assert "Security violation" in res or "Error" in res

