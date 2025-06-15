# langgraph_app/nodes/tool_executor_node.py

from typing import Dict, Any
from tools.query_dataframe_tool import query_tool
import pandas as pd
from langchain_core.runnables import RunnableLambda

# Sample DataFrame (you may load this from CSV in future)
data = {
    "Date": ["2025-06-04", "2025-06-10", "2025-06-15", "2025-05-22", "2025-06-20"],
    "Category": ["Subscriptions", "Shopping", "Groceries", "Shopping", "Rent"],
    "Amount": [485.52, 1450.00, 750.25, 1200.00, 2300.00],
    "Notes": ["Netflix", "Flipkart", "Big Bazaar", "Amazon", "Monthly Rent"]
}
df = pd.DataFrame(data)

def tool_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    tool_input = state.get("tool_input")

    if not tool_input or not isinstance(tool_input, dict):
        return {**state, "result": "❌ Tool execution failed: invalid tool_input"}

    try:
        full_input = {"df": df, **tool_input}
        result = query_tool.invoke(full_input)
        return {**state, "result": result}

    except Exception as e:
        return {**state, "result": f"❌ Tool execution failed: {e}"}

tool_executor_node = RunnableLambda(tool_executor_node)
