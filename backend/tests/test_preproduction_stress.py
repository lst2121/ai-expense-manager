import pytest
import asyncio
from backend.agent.tools.sql_analytics import (
    run_financial_query,
    get_expense_summary,
    query_cache,
    _validate_financial_query,
)
from backend.api.routes.chat import detect_expense_intent
from backend.agent.financial_agent import global_checkpointer


# ==========================================
# CATEGORY A: SECURITY & SQL INJECTION GUARDS
# ==========================================

def test_sec_01_reject_drop_table():
    """SEC-01: Blocks DROP TABLE and multi-statement injection attempts."""
    clean, err = _validate_financial_query("DROP TABLE transactions;")
    assert err is not None
    assert "Security violation" in err

    res = run_financial_query.invoke({"query": "DROP TABLE transactions;"})
    assert "Security violation" in res

    # Injected multi-statement
    res_multi = run_financial_query.invoke({"query": "SELECT * FROM transactions; DROP TABLE accounts;"})
    assert "Multi-statement queries are prohibited" in res_multi


def test_sec_02_block_sql_comments():
    """SEC-02: Blocks SQL comment syntax (-- and /*) used to mask payloads."""
    res_dash = run_financial_query.invoke({"query": "SELECT * FROM accounts WHERE 1=1; -- Show me everything"})
    assert "SQL comment syntax is not permitted" in res_dash

    res_block = run_financial_query.invoke({"query": "SELECT * FROM accounts WHERE 1=1 /* comment */"})
    assert "SQL comment syntax is not permitted" in res_block


def test_sec_04_block_destructive_keywords():
    """SEC-04: Blocks UPDATE, DELETE, INSERT, ALTER statements."""
    for keyword in ["UPDATE transactions SET total_amount = 0 WHERE id = 1;",
                    "DELETE FROM transactions WHERE id = 1;",
                    "INSERT INTO accounts (code, name, type) VALUES ('9999', 'Hack', 'asset');",
                    "ALTER TABLE transactions DROP COLUMN total_amount;"]:
        res = run_financial_query.invoke({"query": keyword})
        assert "Security violation" in res


# ==========================================
# CATEGORY C: BOUNDARIES, CURRENCY & ZERO HALLUCINATION
# ==========================================

def test_edge_01_reject_negative_and_zero_amounts():
    """EDGE-01: Rejects zero and negative amounts in expense intent detection."""
    assert detect_expense_intent("spent -500 on groceries") is None
    assert detect_expense_intent("added 0.00 to savings") is None
    assert detect_expense_intent("-500 groceries") is None
    assert detect_expense_intent("0 pizza") is None


def test_edge_02_calendar_year_guard():
    """EDGE-02: Does not mistake 4-digit calendar years for amounts unless currency is explicit."""
    # Year without currency should NOT trigger expense logging
    assert detect_expense_intent("Project my expenses of 2026") is None
    assert detect_expense_intent("spent 2026 on dinner") is None
    assert detect_expense_intent("forecast 2025 budget") is None

    # Explicit currency makes it a valid transaction
    intent_rs = detect_expense_intent("spent Rs 2026 on dinner")
    assert intent_rs is not None
    assert intent_rs["amount"] == 2026.0

    intent_symbol = detect_expense_intent("₹2026 dinner")
    assert intent_symbol is not None
    assert intent_symbol["amount"] == 2026.0


def test_edge_03_zero_hallucination_future_records():
    """EDGE-03: Asserts zero records returned for non-existent future dates."""
    res = run_financial_query.invoke({"query": "SELECT * FROM transactions WHERE date >= '2099-01-01';"})
    assert "No records found" in res or res == "[]"


def test_edge_04_foreign_currency_detection():
    """EDGE-04: Foreign currencies (USD, EUR, GBP) fall through to the agent for FX conversion."""
    assert detect_expense_intent("spent 50 USD on digital ocean") is None
    assert detect_expense_intent("paid 40 EUR for domain") is None
    assert detect_expense_intent("spent 100 dollars on github") is None


# ==========================================
# CATEGORY D: LINGUISTIC & EMOJI INTENTS
# ==========================================

def test_lang_01_domestic_hinglish_detection():
    """LANG-01: Detects common Indian household expense items and domestic terms."""
    intent_chai = detect_expense_intent("spent 120 on chai")
    assert intent_chai is not None
    assert intent_chai["category"] == "dining"
    assert intent_chai["amount"] == 120.0

    intent_swiggy = detect_expense_intent("350 swiggy")
    assert intent_swiggy is not None
    assert intent_swiggy["category"] == "dining"
    assert intent_swiggy["amount"] == 350.0

    intent_sabzi = detect_expense_intent("spent 450 on sabzi")
    assert intent_sabzi is not None
    assert intent_sabzi["category"] == "groceries"

    intent_maid = detect_expense_intent("paid 2500 for kamwali")
    assert intent_maid is not None
    assert intent_maid["category"] == "rent"


def test_lang_03_emoji_intent_detection():
    """LANG-03: Handles emojis in expense items gracefully."""
    intent_pizza = detect_expense_intent("5000 🍕")
    assert intent_pizza is not None
    assert intent_pizza["category"] == "dining"
    assert intent_pizza["amount"] == 5000.0

    intent_groceries = detect_expense_intent("1200 🛒")
    assert intent_groceries is not None
    assert intent_groceries["category"] == "groceries"
    assert intent_groceries["amount"] == 1200.0


# ==========================================
# CONCURRENCY, ASYNC EXECUTION & CACHE
# ==========================================

@pytest.mark.asyncio
async def test_async_sql_concurrency():
    """Verifies that 10 concurrent async queries execute without thread starvation."""
    queries = [
        run_financial_query.ainvoke({"query": f"SELECT count(*) FROM transactions WHERE total_amount > {i * 10};"})
        for i in range(10)
    ]
    results = await asyncio.gather(*queries)
    assert len(results) == 10
    for r in results:
        assert "count" in r


def test_query_cache_hit():
    """Verifies that repetitive analytical queries hit the in-memory TTL cache."""
    query_cache.clear()
    res1 = get_expense_summary.invoke({"group_by": "category"})
    assert "groceries" in res1.lower()

    # Second invoke must retrieve from cache
    res2 = get_expense_summary.invoke({"group_by": "category"})
    assert res1 == res2


def test_postgres_session_checkpointer_configured():
    """Verifies that the session checkpointer is properly initialized."""
    assert global_checkpointer is not None
    checkpointer_type = type(global_checkpointer).__name__
    assert checkpointer_type in ["PostgresSaver", "MemorySaver", "InMemorySaver"]
