"""
Integration & Regression Tests for Chat Modernization and Enterprise Scale Data
- Dynamic contextual suggestion endpoints (English and Hindi)
- Chat feedback persistence (rating + comment)
- Enterprise synthetic database integrity (>= 6000 transactions, 2024-2026 coverage, double-entry balance)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.api.main import app
from backend.database.connection import SyncSessionLocal

client = TestClient(app)


def test_dynamic_suggestions_english():
    response = client.get("/api/chat/suggestions?language=en")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    suggestions = data["suggestions"]
    assert len(suggestions) >= 3
    assert any("reconcil" in s.lower() or "audit" in s.lower() for s in suggestions)


def test_dynamic_suggestions_hindi():
    response = client.get("/api/chat/suggestions?language=hi")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) >= 3
    # Verify Hindi script or localized text present
    assert any("लेनदेन" in s or "खर्च" in s or "खाते" in s for s in data["suggestions"])


def test_chat_feedback_submission():
    payload = {
        "message_id": "test_msg_pytest_999",
        "rating": "down",
        "comment": "Test feedback: formatting was slightly off",
        "turn_metrics": {
            "query": "pytest test query",
            "tools_called": ["sql_analytics_query"]
        }
    }
    response = client.post("/api/chat/feedback", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "feedback_id" in res_data

    # Verify directly in the database
    with SyncSessionLocal() as db:
        row = db.execute(
            text("SELECT rating, comment FROM chat_feedback WHERE message_id = :mid"),
            {"mid": "test_msg_pytest_999"}
        ).fetchone()
        assert row is not None
        assert row[0] == "down"
        assert "formatting was slightly off" in row[1]


def test_enterprise_dataset_scale_and_balance():
    with SyncSessionLocal() as db:
        # Check transaction count
        tx_count = db.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        assert tx_count >= 6000, f"Expected >= 6000 transactions, found {tx_count}"

        # Check multi-year coverage
        years = db.execute(text("SELECT DISTINCT EXTRACT(YEAR FROM date)::int FROM transactions ORDER BY 1")).fetchall()
        year_list = [y[0] for y in years]
        assert 2024 in year_list
        assert 2025 in year_list
        assert 2026 in year_list

        # Check double-entry balance: SUM(debit) == SUM(credit)
        balance = db.execute(text("SELECT ROUND(COALESCE(SUM(debit) - SUM(credit), 0), 2) FROM journal_entries")).scalar()
        assert balance == 0.00, f"Double-entry ledger is not balanced: net discrepancy = {balance}"

        # Check unreconciled transactions exist for audit prompts
        unrec = db.execute(text("SELECT COUNT(*) FROM transactions WHERE is_reconciled = FALSE")).scalar()
        assert unrec > 0, "Expected at least some unreconciled transactions for realistic audit tests"
