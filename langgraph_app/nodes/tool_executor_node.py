# langgraph_app/nodes/tool_executor_node.py

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from tools.query_dataframe_tool import query_tool
from tools.fallback_tool import fallback_tool
from tools.top_expenses_tool import top_expenses_tool
from tools.monthly_expenses_tool import monthly_expenses_tool
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
    arguments["df"] = df  # Inject test DataFrame

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
        return {
            **state,
            "result": result,
            "invoked_tool": tool_name
        }
    except Exception as e:
        return {
            **state,
            "result": f"❌ Tool execution failed: {e}",
            "invoked_tool": tool_name
        }

tool_executor_node = RunnableLambda(tool_executor_node)
