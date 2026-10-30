"""
Unit and Integration Tests for PostgreSQL Chat Session Persistence & Multi-Turn Thread Management
- Session CRUD: Create, Read, Update (pinning/renaming), and Delete
- Message Storage: User queries and streaming assistant responses with chart_spec & tool_calls
- Prompt Multilingual Tool Localization Rule verification
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.api.main import app
from backend.database.connection import SyncSessionLocal
from backend.agent.prompts import EXECUTIVE_COPILOT_PROMPT

client = TestClient(app)


def test_session_lifecycle_crud():
    # 1. Create a new chat session
    create_res = client.post("/api/chat/sessions", json={"title": "October Entertainment Audit"})
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["status"] == "success"
    session = create_data["session"]
    session_id = session["id"]
    assert session["title"] == "October Entertainment Audit"
    assert session["is_pinned"] is False

    # 2. Verify session appears in session list
    list_res = client.get("/api/chat/sessions")
    assert list_res.status_code == 200
    sessions = list_res.json()["sessions"]
    found = next((s for s in sessions if s["id"] == session_id), None)
    assert found is not None
    assert found["title"] == "October Entertainment Audit"

    # 3. Pin and rename session via PATCH
    patch_res = client.patch(
        f"/api/chat/sessions/{session_id}",
        json={"is_pinned": True, "title": "📌 2026 Entertainment & Movies Breakdown"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "success"

    # Verify updated properties in DB
    with SyncSessionLocal() as db:
        row = db.execute(
            text("SELECT title, is_pinned FROM chat_sessions WHERE id = :sid"),
            {"sid": session_id}
        ).fetchone()
        assert row is not None
        assert row[0] == "📌 2026 Entertainment & Movies Breakdown"
        assert row[1] is True

    # 4. Fetch session detail
    detail_res = client.get(f"/api/chat/sessions/{session_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()["session"]
    assert detail["title"] == "📌 2026 Entertainment & Movies Breakdown"
    assert detail["is_pinned"] is True
    assert isinstance(detail["messages"], list)

    # 5. Delete session
    del_res = client.delete(f"/api/chat/sessions/{session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify session is gone from DB
    with SyncSessionLocal() as db:
        cnt = db.execute(
            text("SELECT count(*) FROM chat_sessions WHERE id = :sid"),
            {"sid": session_id}
        ).scalar()
        assert cnt == 0


def test_session_message_persistence_and_cascade():
    # Create test session
    create_res = client.post("/api/chat/sessions", json={"title": "UPI Discrepancies Thread"})
    session_id = create_res.json()["session"]["id"]

    try:
        # Simulate inserting messages directly into chat_messages
        with SyncSessionLocal() as db:
            db.execute(
                text("""
                    INSERT INTO chat_messages (id, session_id, role, content, chart_spec, tool_calls, created_at)
                    VALUES (:mid1, :sid, 'user', 'What was my spending on BESCOM in 2026?', NULL, NULL, NOW()),
                           (:mid2, :sid, 'assistant', 'Your BESCOM electricity spending was ₹42,500.00.', '{"__chart__": true, "type": "bar"}', '[{"tool": "sql_analytics_query"}]', NOW())
                """),
                {"mid1": "msg_test_user_01", "mid2": "msg_test_asst_01", "sid": session_id}
            )
            db.commit()

        # Retrieve messages via GET /api/chat/sessions/{session_id}
        detail_res = client.get(f"/api/chat/sessions/{session_id}")
        assert detail_res.status_code == 200
        messages = detail_res.json()["session"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert "BESCOM" in messages[0]["content"]
        assert messages[1]["role"] == "assistant"
        assert messages[1]["chart_spec"] is not None
        assert messages[1]["tool_calls"] is not None

        # Verify cascade delete: deleting session must delete messages
        del_res = client.delete(f"/api/chat/sessions/{session_id}")
        assert del_res.status_code == 200

        with SyncSessionLocal() as db:
            remaining_msgs = db.execute(
                text("SELECT count(*) FROM chat_messages WHERE session_id = :sid"),
                {"sid": session_id}
            ).scalar()
            assert remaining_msgs == 0

    finally:
        # Cleanup if needed
        with SyncSessionLocal() as db:
            db.execute(text("DELETE FROM chat_sessions WHERE id = :sid"), {"sid": session_id})
            db.commit()


def test_prompt_multilingual_localization_rule():
    # Verify the master prompt strictly instructs localization of tool arguments
    assert "STRICT LOCALIZATION RULE FOR TOOLS" in EXECUTIVE_COPILOT_PROMPT
    assert "generate_chart_spec" in EXECUTIVE_COPILOT_PROMPT
    assert "Hinglish Mirroring" in EXECUTIVE_COPILOT_PROMPT
