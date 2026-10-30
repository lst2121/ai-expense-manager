import os
import logging
from typing import Optional, Any
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
logger = logging.getLogger(__name__)

from backend.agent.llm_factory import get_llm
from backend.agent.prompts import ACCOUNTING_SYSTEM_PROMPT
from backend.agent.tools.temporal_tool import get_current_datetime
from backend.agent.tools.web_search_tool import web_search
from backend.agent.tools.sql_analytics import run_financial_query, get_expense_summary
from backend.agent.tools.chart_tool import generate_chart_spec
from backend.agent.tools.extractor_tool import inspect_uploaded_document

# In-memory checkpointer fallback
global_checkpointer = MemorySaver()


def get_accounting_tools():
    """Returns list of native LangChain tools for the financial controller."""
    return [
        get_current_datetime,
        web_search,
        run_financial_query,
        get_expense_summary,
        generate_chart_spec,
        inspect_uploaded_document,
    ]


def create_financial_agent(
    llm: Optional[Any] = None,
    checkpointer: Optional[Any] = None,
    system_prompt: Optional[str] = None
):
    """
    Constructs a LangGraph ReAct agent pre-equipped with financial accounting tools,
    a state checkpointer, and system instructions.
    """
    if llm is None:
        llm = get_llm()

    if checkpointer is None:
        checkpointer = global_checkpointer

    prompt_to_use = system_prompt or ACCOUNTING_SYSTEM_PROMPT
    tools = get_accounting_tools()

    return create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        prompt=prompt_to_use,
    )
