from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from expense_manager import config

llm = ChatDeepSeek(
    temperature=config.TEMPERATURE,
    model=config.DEEPSEEK_MODEL_NAME,
    api_key=SecretStr(config.DEEPSEEK_API_KEY),
    base_url=config.BASE_URL
)

SYSTEM_PROMPT = """
You are an AI assistant helping to extract structured tool instructions from a user's expense-related query.

You MUST return a Python dictionary with keys depending on the operation:

Operations:
1. "top_n_expenses"
    - category: optional (e.g., "Groceries", "Rent")
    - n: optional (default is 3)

2. "list_month_expenses"
    - month: required (format: "YYYY-MM")

Examples:
User: Show expenses for June 2025
-> {"operation": "list_month_expenses", "month": "2025-06"}

User: Top 2 expenses in groceries
-> {"operation": "top_n_expenses", "category": "Groceries", "n": 2}

User: What did I spend most on?
-> {"operation": "top_n_expenses"}
"""

def rewrite_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["query"]
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {query}\n->"

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        tool_input = eval(content.strip())

        return {**state, "tool_input": tool_input}

    except Exception as e:
        return {**state, "tool_input": None, "result": f"❌ Failed to parse tool input: {e}"}

rewrite_agent_node = RunnableLambda(rewrite_agent_node)
