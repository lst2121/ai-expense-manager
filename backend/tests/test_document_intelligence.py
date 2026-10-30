import pytest
import uuid
import httpx
from backend.agent.tools.extractor_tool import analyze_document_with_llm
from backend.database.connection import AsyncSessionLocal
from sqlalchemy import text


@pytest.mark.asyncio
async def test_non_financial_document_classification():
    """
    Verify that an informational document (e.g. FAQs for India Leavers)
    is accurately classified as non-financial with is_financial=False and 0 transactions.
    """
    faq_text = (
        "FAQs for India Leavers - October 2026 Guidelines.\n"
        "Question 1: What should I do with my EPF account when moving abroad?\n"
        "Answer: Your EPF account will continue to earn interest until you reach 58 years of age.\n"
        "Question 2: How do I convert my resident savings bank account into an NRO account?\n"
        "Answer: Contact your branch manager with your overseas visa, address proof, and passport copy."
    )

    res = await analyze_document_with_llm(
        text_content=faq_text,
        filename="FAQs_for_India_Leavers_October_2026.pdf",
        provider="deepseek"
    )

    assert res["is_financial"] is False
    assert res["document_type"] == "non_financial_document"
    assert len(res.get("transactions", [])) == 0
    assert "EPF" in res.get("summary", "") or "India" in res.get("summary", "") or "overseas" in res.get("summary", "") or "resident" in res.get("summary", "")


@pytest.mark.asyncio
async def test_ingest_endpoint_persists_document_in_session():
    """
    Verify that /api/chat/ingest commits the document summary to chat_messages
    so that multi-turn conversational memory is preserved.
    """
    session_id = f"test-doc-sess-{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Ingest non-financial document
        response = await client.post(
            "/api/chat/ingest",
            data={
                "raw_text": "HR Guidelines 2026: Maternity leave policy, holiday calendar, and remote work stipends.",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["is_financial"] is False
        assert data["widget_type"] == "document_summary"
        assert data["receipt"] is None

        # Verify that chat_messages in PostgreSQL now holds the record!
        async with AsyncSessionLocal() as db_session:
            msgs = await db_session.execute(
                text("SELECT role, content FROM chat_messages WHERE session_id = :sid ORDER BY created_at ASC"),
                {"sid": session_id}
            )
            rows = msgs.fetchall()
            assert len(rows) == 2
            assert rows[0][0] == "user"
            assert "Uploaded document" in rows[0][1]
            assert rows[1][0] == "assistant"
            assert "Uploaded Document Analysis" in rows[1][1]

            # Cleanup test session
            await db_session.execute(text("DELETE FROM chat_messages WHERE session_id = :sid"), {"sid": session_id})
            await db_session.execute(text("DELETE FROM chat_sessions WHERE id = :sid"), {"sid": session_id})
            await db_session.commit()
