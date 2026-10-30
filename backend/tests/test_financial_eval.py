import pytest
from typing import Sequence, Any, Callable
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.checkpoint.memory import MemorySaver

from backend.agent.financial_agent import create_financial_agent, get_accounting_tools
from backend.agent.prompts import ACCOUNTING_SYSTEM_PROMPT


class ToolEnabledFakeChatModel(GenericFakeChatModel):
    """Fake chat model implementing bind_tools for deterministic offline testing."""
    def bind_tools(self, tools: Sequence[Any], **kwargs: Any):
        return self


def test_agent_initialization():
    """Verify financial agent graph structure and tools binding."""
    tools = get_accounting_tools()
    tool_names = {t.name for t in tools}

    assert "run_financial_query" in tool_names
    assert "get_expense_summary" in tool_names
    assert "generate_chart_spec" in tool_names
    assert "get_current_datetime" in tool_names
    assert "web_search" in tool_names

    memory = MemorySaver()
    fake_llm = ToolEnabledFakeChatModel(messages=iter([
        AIMessage(content="Total expenditure is $116,725.55 based on current general ledger.")
    ]))

    agent = create_financial_agent(llm=fake_llm, checkpointer=memory)
    assert agent is not None

    # Test single-turn conversation
    config = {"configurable": {"thread_id": "test-eval-thread"}}
    result = agent.invoke({"messages": [HumanMessage(content="What is total spend?")]}, config=config)

    assert "messages" in result
    last_msg = result["messages"][-1]
    assert "116,725.55" in last_msg.content


def test_agent_tool_calling_trajectory():
    """Verify tool call dispatch and execution in graph state."""
    # Sequence:
    # 1. LLM requests get_expense_summary tool call
    # 2. Graph executes tool and returns ToolMessage
    # 3. LLM returns final answer
    msg_1 = AIMessage(
        content="",
        tool_calls=[{
            "id": "call_123",
            "name": "get_expense_summary",
            "args": {"group_by": "category"}
        }]
    )
    msg_2 = AIMessage(content="Analyzed the breakdown: top category is Rent.")

    fake_llm = ToolEnabledFakeChatModel(messages=iter([msg_1, msg_2]))
    agent = create_financial_agent(llm=fake_llm, checkpointer=MemorySaver())

    config = {"configurable": {"thread_id": "eval-tool-thread"}}
    res = agent.invoke({"messages": [HumanMessage(content="Break down expenses")]}, config=config)

    messages = res["messages"]
    assert len(messages) >= 3
    # Check that a ToolMessage was produced by get_expense_summary
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_msgs) >= 1
    assert "grand_total" in tool_msgs[0].content
    assert "breakdown" in tool_msgs[0].content
