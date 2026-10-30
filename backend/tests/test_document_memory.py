import pytest
import uuid
import json
import httpx


@pytest.mark.asyncio
async def test_followup_document_conversational_memory():
    """
    Verify that after uploading an informational document, asking
    'What this doc was about' in the same session recalls the document analysis
    and never says 'I don't see any document'.
    """
    session_id = f"test-mem-sess-{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Step 1: Ingest document
        ingest_res = await client.post(
            "/api/chat/ingest",
            data={
                "raw_text": (
                    "FAQs for India Leavers - October 2026 Guidelines.\n"
                    "This document is an HR FAQ for departing Norstella India employees, covering notice periods, "
                    "garden leave, last working day, early release, final pay timing, relieving letters, and Form-16."
                ),
                "session_id": session_id,
            }
        )
        assert ingest_res.status_code == 200
        assert ingest_res.json()["is_financial"] is False

        # Step 2: Stream follow-up query: "What this doc was about"
        async with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "message": "What this doc was about",
                "session_id": session_id,
                "thread_id": session_id,
                "provider": "deepseek",
            }
        ) as response:
            assert response.status_code == 200
            accumulated_tokens = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[5:].strip())
                        if "token" in data:
                            accumulated_tokens.append(data["token"])
                    except Exception:
                        pass

            full_reply = "".join(accumulated_tokens).lower()
            print("Full follow-up reply:", full_reply)

            # Assert conversational memory works!
            assert "i don't see any document" not in full_reply
            assert any(k in full_reply for k in ["norstella", "faq", "hr", "leavers", "notice period", "document"])


@pytest.mark.asyncio
async def test_long_horizon_document_retention_after_multiple_turns():
    """
    Verify that even after multiple intermediate conversational turns (financial queries),
    asking 'do you know about my norstella doc which i uploaded' still recalls the exact
    uploaded document without context amnesia, and never outputs stray empty backtick artifacts (` `).
    """
    session_id = f"test-long-mem-{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Step 1: Upload Norstella HR Leavers document
        ingest_res = await client.post(
            "/api/chat/ingest",
            data={
                "raw_text": (
                    "Norstella India Leavers Policy - October 2026.\n"
                    "1. Notice Period: Mandatory 90 calendar days notice period applies for all full-time India employees.\n"
                    "2. Garden Leave: The company may place departing employees on garden leave subject to VP approval.\n"
                    "3. Last Working Day (LWD): Determined mutually based on project handover status.\n"
                    "4. Full and Final Settlement (F&F): Processed within 45 days following the official last working day.\n"
                    "5. Form-16: Form 16 Part A and Part B will be issued via the HR payroll portal in June following FY close."
                ),
                "session_id": session_id,
            }
        )
        assert ingest_res.status_code == 200

        # Step 2: Multiple intermediate turns
        intermediate_queries = [
            "3500 pizza",
            "What is my spending this year?",
            "Show recent transactions"
        ]
        for q in intermediate_queries:
            async with client.stream(
                "POST",
                "/api/chat/stream",
                json={
                    "message": q,
                    "session_id": session_id,
                    "thread_id": session_id,
                    "provider": "deepseek",
                }
            ) as inter_resp:
                assert inter_resp.status_code == 200
                async for _ in inter_resp.aiter_lines():
                    pass

        # Step 3: Now ask about the uploaded norstella doc after several turns
        async with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "message": "do you know about my norstella doc which i uploaded",
                "session_id": session_id,
                "thread_id": session_id,
                "provider": "deepseek",
            }
        ) as follow_resp:
            assert follow_resp.status_code == 200
            tokens = []
            async for line in follow_resp.aiter_lines():
                if line.startswith("data:"):
                    try:
                        d = json.loads(line[5:].strip())
                        if "token" in d:
                            tokens.append(d["token"])
                    except Exception:
                        pass

            reply = "".join(tokens)
            reply_lower = reply.lower()
            print("Multi-turn document reply:", reply)

            # Assert no memory amnesia:
            assert "i don't see any document" not in reply_lower
            assert "did not reach my working context" not in reply_lower
            assert "i don't have the text" not in reply_lower
            assert any(k in reply_lower for k in ["norstella", "notice period", "90 days", "garden leave", "f&f", "leavers", "settlement", "form-16"])

            # Assert NO stray empty backticks (` ` or `  `)
            assert "` `" not in reply
            assert "`  `" not in reply


