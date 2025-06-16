from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from tools.query_dataframe_tool import query_tool
from tools.fallback_tool import fallback_tool
from tools.top_expenses_tool import top_expenses_tool
from tools.monthly_expenses_tool import monthly_expenses_tool
from tools.sum_category_expenses_tool import sum_category_expenses_tool
from tools.date_range_expense_tool import date_range_expense_tool
from tools.summarize_memory_tool import summarize_memory_tool
from tools.compare_months_tool import compare_months_tool
import pandas as pd

# Sample dataframe (for test mode)
data = {
    "Date": ["2025-06-20", "2025-06-15", "2025-06-10", "2025-06-04", "2025-05-22", "2025-05-10"],
    "Category": ["Rent", "Groceries", "Shopping", "Subscriptions", "Shopping", "Groceries"],
    "Amount": [2300, 750.25, 1450, 485.52, 1200, 670],
    "Notes": ["Monthly Rent", "Big Bazaar", "Flipkart", "Netflix", "Amazon", "Local Store"]
}
df = pd.DataFrame(data)

# Tool map
TOOL_REGISTRY = {
    # "query_tool": query_tool,
    "fallback_tool": fallback_tool,
    "top_expenses_tool": top_expenses_tool,
    "monthly_expenses_tool": monthly_expenses_tool,
    "sum_category_expenses_tool": sum_category_expenses_tool,
    "date_range_expense_tool": date_range_expense_tool,
    "summarize_memory_tool": summarize_memory_tool,
    "compare_months_tool": compare_months_tool,
}

def tool_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    tool_input = state.get("tool_input")
    if not tool_input:
        return {
            **state,
            "result": "❌ Missing tool_input",
            "invoked_tool": "None"
        }

    tool_name = tool_input.get("tool_name")
    arguments = tool_input.get("arguments", {})

    # ✅ Inject df for all tools except summarize
    if tool_name != "summarize_memory_tool":
        arguments["df"] = state.get("df")

    # ✅ Inject memory if needed
    if tool_name == "summarize_memory_tool":
        arguments["memory"] = state.get("memory", [])

    if not tool_name or tool_name not in TOOL_REGISTRY:
        return {
            **state,
            "result": f"❌ Unknown tool: {tool_name}",
            "invoked_tool": tool_name or "None"
        }

    try:
        print(f"⚙️ Executing Tool: {tool_name}")
        print(f"📦 Arguments: {arguments}")
        tool = TOOL_REGISTRY[tool_name]
        result = tool.invoke(arguments)

        # ✅ If tool returns dict with text, extract it
        text_result = result.get("text", result) if isinstance(result, dict) else result

        # ✅ Clean memory
        memory_entry = {
            "query": state["query"],
            "tool_name": tool_name,
            "tool_args": {
                k: v for k, v in arguments.items()
                if k not in ["df", "memory"]
            },
            "result": text_result
        }

        memory = state.get("memory", [])
        memory.append(memory_entry)

        return {
            **state,
            "result": text_result,
            "invoked_tool": tool_name,
            "memory": memory,
        }

    except Exception as e:
        return {
            **state,
            "result": f"❌ Tool execution failed: {e}",
            "invoked_tool": tool_name
        }

tool_executor_node = RunnableLambda(tool_executor_node)
