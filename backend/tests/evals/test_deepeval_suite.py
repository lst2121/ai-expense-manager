import pytest
import os
import json
import httpx
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    HallucinationMetric,
    GEval,
)
from backend.tests.evals.eval_llm import DeepEvalCustomModel


@pytest.fixture(scope="module")
def eval_judge():
    """Shared LLM judge powered by DeepSeek or Gemini Flash (no OpenAI key required)."""
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")
    return DeepEvalCustomModel(provider=provider)


@pytest.mark.asyncio
async def test_deepeval_financial_faithfulness(eval_judge):
    """
    Evaluates that the assistant's financial figures and vendor totals
    are strictly faithful to the general ledger SQL context without hallucination.
    """
    query = "Break down my Entertainment spending for 2026"
    retrieval_context = [
        "In 2026, total entertainment spend is ₹22,45,475 across 227 transactions.",
        "Top vendors in Entertainment: Steam Games (₹7,02,539.00), BookMyShow Cinema (₹5,88,433.00), Timezone Arcade (₹5,49,709.00), PVR Inox Movies (₹4,04,794.00).",
        "Peak spending month was July 2026 at ₹4,64,581.00."
    ]

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=35.0) as client:
        async with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "message": query,
                "session_id": "eval-sess-faithfulness",
                "thread_id": "eval-sess-faithfulness",
                "provider": "deepseek",
            }
        ) as response:
            assert response.status_code == 200
            tokens = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        d = json.loads(line[5:].strip())
                        if "token" in d:
                            tokens.append(d["token"])
                    except Exception:
                        pass
            actual_output = "".join(tokens)

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context
    )

    metric = FaithfulnessMetric(threshold=0.75, model=eval_judge, include_reason=True)
    metric.measure(test_case)
    print(f"\n[DeepEval Faithfulness] Score: {metric.score} | Reason: {metric.reason}")
    assert metric.score >= 0.70, f"Faithfulness score {metric.score} below threshold: {metric.reason}"


@pytest.mark.asyncio
async def test_deepeval_answer_relevancy(eval_judge):
    """
    Evaluates that macroeconomic and market queries are answered directly
    and factually without unsolicited personal financial lectures.
    """
    query = "What are current inflation trends and RBI repo rates in India?"

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=35.0) as client:
        async with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "message": query,
                "session_id": "eval-sess-relevancy",
                "thread_id": "eval-sess-relevancy",
                "provider": "deepseek",
            }
        ) as response:
            assert response.status_code == 200
            tokens = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        d = json.loads(line[5:].strip())
                        if "token" in d:
                            tokens.append(d["token"])
                    except Exception:
                        pass
            actual_output = "".join(tokens)

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output
    )

    metric = AnswerRelevancyMetric(threshold=0.75, model=eval_judge, include_reason=True)
    metric.measure(test_case)
    print(f"\n[DeepEval Relevancy] Score: {metric.score} | Reason: {metric.reason}")
    assert metric.score >= 0.70, f"Relevancy score {metric.score} below threshold: {metric.reason}"


@pytest.mark.asyncio
async def test_deepeval_financial_geval_criteria(eval_judge):
    """
    Custom G-Eval Metric evaluating:
    1. Proper Indian Rupee formatting with currency symbol (₹) and Indian comma grouping.
    2. Professional, supportive tone without demeaning net worth.
    3. Proper presentation of accounting details (no unsolicited raw debit/credit code dumps).
    """
    query = "How much did I spend on dining last month?"
    context = ["Last month Dining & Catering total expenditure was ₹28,450.00 across 34 transactions."]

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=35.0) as client:
        async with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "message": query,
                "session_id": "eval-sess-geval",
                "thread_id": "eval-sess-geval",
                "provider": "deepseek",
            }
        ) as response:
            assert response.status_code == 200
            tokens = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        d = json.loads(line[5:].strip())
                        if "token" in d:
                            tokens.append(d["token"])
                    except Exception:
                        pass
            actual_output = "".join(tokens)

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=context
    )

    geval_metric = GEval(
        name="Financial Protocol & Tone Metric",
        criteria=(
            "Evaluate whether the response:\n"
            "1. Uses Indian Rupee symbols (₹) and clean Indian comma grouping for amounts (e.g. ₹28,450.00).\n"
            "2. Answers the spend question directly in the opening sentence.\n"
            "3. Does not insult or lecture the user.\n"
            "4. Concludes with helpful actionable suggestions."
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=eval_judge,
        threshold=0.70
    )

    geval_metric.measure(test_case)
    print(f"\n[DeepEval G-Eval] Score: {geval_metric.score} | Reason: {geval_metric.reason}")
    assert geval_metric.score >= 0.65, f"G-Eval score {geval_metric.score} below threshold: {geval_metric.reason}"


@pytest.mark.asyncio
async def test_deepeval_document_grounding(eval_judge):
    """
    Evaluates that answers about uploaded documents (e.g. Norstella India Leavers FAQ)
    are strictly grounded in the document text and do not invent policy terms.
    """
    doc_context = [
        "Norstella India Leavers FAQ - October 2026:\n"
        "1. Notice Period: Mandatory 90 calendar days notice applies to all India permanent staff.\n"
        "2. Garden Leave: Subject to VP and HR approval, employee may be put on garden leave.\n"
        "3. Full and Final Settlement (F&F): Will be disbursed within 45 days after Last Working Day (LWD).\n"
        "4. Form-16: Part A and Part B will be emailed by the payroll team in June following FY close."
    ]

    query = "What is the notice period and garden leave policy in the uploaded Norstella document?"

    # We evaluate against the model's actual answer when provided with the document
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=35.0) as client:
        # Step 1: Ingest document into active session
        session_id = "eval-sess-doc-grounding"
        await client.post(
            "/api/chat/ingest",
            data={
                "raw_text": doc_context[0],
                "session_id": session_id,
            }
        )

        # Step 2: Query the document
        async with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "message": query,
                "session_id": session_id,
                "thread_id": session_id,
                "provider": "deepseek",
            }
        ) as response:
            assert response.status_code == 200
            tokens = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        d = json.loads(line[5:].strip())
                        if "token" in d:
                            tokens.append(d["token"])
                    except Exception:
                        pass
            actual_output = "".join(tokens)

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        context=doc_context,
        retrieval_context=doc_context
    )

    hallucination_metric = HallucinationMetric(threshold=0.30, model=eval_judge)
    hallucination_metric.measure(test_case)
    print(f"\n[DeepEval Hallucination] Score: {hallucination_metric.score} | Reason: {hallucination_metric.reason}")
    assert hallucination_metric.score <= 0.35, f"Hallucination score {hallucination_metric.score} exceeded threshold: {hallucination_metric.reason}"

