# langgraph_app/nodes/rewrite_agent_node.py

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr
from expense_manager import config
import json

# Tool routing map
OPERATION_TO_TOOL = {
    "top_n_expenses": "top_expenses_tool",
    "list_month_expenses": "monthly_expenses_tool",
}

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
        print(f"\n🧠 LLM RESPONSE: {content}")  # Debug log

        # Use json.loads instead of eval for safety
        parsed = json.loads(content.strip())

        operation = parsed.get("operation")
        if not operation or operation not in OPERATION_TO_TOOL:
            return {
                **state,
                "result": f"❌ Unknown or missing operation: {operation}",
                "tool_input": None,
                "invoked_tool": "None"
            }

        tool_input = {
            "tool_name": OPERATION_TO_TOOL[operation],
            "arguments": {k: v for k, v in parsed.items() if k != "operation"}
        }

        print(f"🛠️ Parsed Tool Input: {tool_input}")  # Debug log

        return {
            **state,
            "tool_input": tool_input,
            "invoked_tool": tool_input["tool_name"]
        }

    except Exception as e:
        return {
            **state,
            "result": f"❌ Failed to parse tool input: {e}",
            "tool_input": None,
            "invoked_tool": "None"
        }

rewrite_agent_node = RunnableLambda(rewrite_agent_node)
