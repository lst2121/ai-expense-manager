from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr
from expense_manager import config
from tools.utils import resolve_time_period  # ✅ Use central util
import json

# Tool routing map
OPERATION_TO_TOOL = {
    "top_n_expenses": "top_expenses_tool",
    "list_month_expenses": "monthly_expenses_tool",
    "sum_category_expenses": "sum_category_expenses_tool",
    "date_range_expense": "date_range_expense_tool",
    "summarize_memory": "summarize_memory_tool",
     "compare_months": "compare_months_tool",
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
    - month: required (format: "YYYY-MM" or relative like "last month")
    - category: optional (e.g., "Shopping", "Food")

3. "sum_category_expenses"
    - category: required (e.g., "Healthcare", "Groceries")
    
4. "date_range_expense"
    - category: optional
    - start_date: required (format: YYYY-MM-DD)
    - end_date: required (format: YYYY-MM-DD)

5. "summarize_memory"
    - No arguments required. Summarizes all past spending memory.

6. "compare_months"
    - month1: required (e.g., "2025-05")
    - month2: required (e.g., "2025-06")
    - category: optional (e.g., "Shopping")

Examples:
User: Show expenses for June 2025
-> {"operation": "list_month_expenses", "month": "2025-06"}

User: Top 2 expenses in groceries
-> {"operation": "top_n_expenses", "category": "Groceries", "n": 2}

User: What did I spend most on?
-> {"operation": "top_n_expenses"}

User: How much did I spend on healthcare?
-> {"operation": "sum_category_expenses", "category": "Healthcare"}

User: How much did I spend between 2025-05-01 and 2025-06-10 on subscription?
-> {"operation": "date_range_expense", "category": "Subscriptions", "start_date": "2025-05-01", "end_date": "2025-06-10"}

User: How much I spend on Shopping last month?
-> {"operation": "list_month_expenses", "category": "Shopping", "month": "last month"}

User: How much did I spend on groceries in May?
-> {"operation": "list_month_expenses", "month": "2025-05", "category": "Groceries"}

User: Summarize my past spending
-> {"operation": "summarize_memory"}

User: Compare May and June spending
-> {"operation": "compare_months", "month1": "2025-05", "month2": "2025-06"}


"""

def rewrite_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["query"]
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {query}\n->"

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        print(f"\n🧠 LLM RESPONSE: {content}")  # Debug log

        parsed = json.loads(content.strip())
        operation = parsed.get("operation")

        if not operation or operation not in OPERATION_TO_TOOL:
            return {
                **state,
                "result": f"❌ Unknown or missing operation: {operation}",
                "tool_input": None,
                "invoked_tool": "None"
            }

        arguments = {k: v for k, v in parsed.items() if k != "operation"}

        # ✅ Normalize time period using shared utility
        if operation == "list_month_expenses" and "month" in arguments:
            arguments["month"] = resolve_time_period(arguments["month"])

        tool_input = {
            "tool_name": OPERATION_TO_TOOL[operation],
            "arguments": arguments
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
