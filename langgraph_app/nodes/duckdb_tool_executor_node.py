"""
DuckDB Tool Executor Node for LangGraph
Uses SQL-based tools for better performance and scalability
"""

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda

# Import DuckDB tools
from duckdb_tools.tools.sum_category_expenses_tool import sum_category_expenses_tool
from duckdb_tools.tools.top_expenses_tool import top_expenses_tool
from duckdb_tools.tools.category_summary_tool import category_summary_tool
from duckdb_tools.tools.monthly_expenses_tool import monthly_expenses_tool

# Import legacy tools (for fallback)
from tools.query_dataframe_tool import query_tool
from tools.fallback_tool import fallback_tool
from tools.monthly_expenses_tool import monthly_expenses_tool as legacy_monthly_expenses_tool
from tools.date_range_expense_tool import date_range_expense_tool
from tools.summarize_memory_tool import summarize_memory_tool
from tools.compare_months_tool import compare_months_tool
from tools.compare_category_tool import compare_category_tool
from tools.average_category_expense_tool import average_category_expense_tool

import pandas as pd

# Tool map with DuckDB tools prioritized
DUCKDB_TOOL_REGISTRY = {
    # 🚀 DuckDB-based tools (SQL-powered)
    "sum_category_expenses_tool": sum_category_expenses_tool,
    "top_expenses_tool": top_expenses_tool,
    "category_summary_tool": category_summary_tool,
    "monthly_expenses_tool": monthly_expenses_tool,
    
    # 📊 Legacy Pandas-based tools (fallback)
    "query_tool": query_tool,
    "fallback_tool": fallback_tool,
    "legacy_monthly_expenses_tool": legacy_monthly_expenses_tool,
    "date_range_expense_tool": date_range_expense_tool,
    "summarize_memory_tool": summarize_memory_tool,
    "compare_months_tool": compare_months_tool,
    "compare_category_tool": compare_category_tool,
    "average_category_expense_tool": average_category_expense_tool,
}

# Operation-to-tool mapping
OPERATION_TO_TOOL = {
    # 🚀 DuckDB operations
    "sum_category_expenses": "sum_category_expenses_tool",
    "top_expenses": "top_expenses_tool",
    "category_summary": "category_summary_tool",
    "list_month_expenses": "monthly_expenses_tool",
    "monthly_expenses": "monthly_expenses_tool",
    
    # 📊 Legacy operations
    "compare_months": "compare_months_tool",
    "legacy_monthly_expenses": "legacy_monthly_expenses_tool",
    "summarize_memory": "summarize_memory_tool",
    "query": "query_tool",
    "fallback": "fallback_tool",
    "date_range_expense": "date_range_expense_tool",
    "compare_category": "compare_category_tool",
    "average_category_expense": "average_category_expense_tool",
}

def duckdb_tool_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute tools with DuckDB support
    Automatically handles both DuckDB and legacy Pandas tools
    """
    tool_input = state.get("tool_input")
    if not tool_input:
        return {
            **state,
            "result": "❌ Missing tool_input",
            "invoked_tool": "None"
        }

    tool_name = tool_input.get("tool_name")
    arguments = tool_input.get("arguments", {})
    operation = tool_input.get("operation")

    # 🧠 If tool_name is missing, try resolving from operation
    if not tool_name and operation:
        tool_name = OPERATION_TO_TOOL.get(operation)

    # 🚀 Handle DuckDB tools (don't need df parameter)
    duckdb_tools = ["sum_category_expenses_tool", "top_expenses_tool", "category_summary_tool", "monthly_expenses_tool"]
    
    if tool_name in duckdb_tools:
        # DuckDB tools use table_name instead of df
        arguments["table_name"] = "expenses"
        
        # Remove df from arguments for DuckDB tools
        if "df" in arguments:
            del arguments["df"]
    else:
        # Legacy tools need df
        if tool_name != "summarize_memory_tool":
            arguments["df"] = state.get("df")

    # ✅ Inject memory for memory-based tools
    if tool_name == "summarize_memory_tool":
        arguments["memory"] = state.get("memory", [])
        arguments["df"] = state.get("df")

    if not tool_name or tool_name not in DUCKDB_TOOL_REGISTRY:
        return {
            **state,
            "result": f"❌ Unknown or missing tool: `{tool_name or operation or 'None'}`",
            "invoked_tool": tool_name or "None"
        }

    try:
        print(f"⚙️ Executing Tool: {tool_name}")
        print(f"📦 Arguments: {arguments}")
        
        tool = DUCKDB_TOOL_REGISTRY[tool_name]
        result = tool.invoke(arguments)

        # ✅ Handle both text-only and text+chart results
        if isinstance(result, dict):
            text_result = result.get("text", str(result))
            chart_result = result.get("chart")
        else:
            text_result = str(result)
            chart_result = None

        # ✅ Append to memory
        memory_entry = {
            "query": state["query"],
            "tool_name": tool_name,
            "tool_args": {
                k: v for k, v in arguments.items()
                if k not in ["df", "memory", "table_name"]
            },
            "answer": text_result,
            "chart": chart_result  # Include chart in memory
        }

        memory = state.get("memory", [])
        memory.append(memory_entry)

        return {
            **state,
            "result": text_result,
            "chart": chart_result,  # Add chart to state
            "invoked_tool": tool_name,
            "memory": memory,
        }

    except Exception as e:
        return {
            **state,
            "result": f"❌ Tool execution failed: {e}",
            "invoked_tool": tool_name
        }

# Create the runnable node
duckdb_tool_executor_node = RunnableLambda(duckdb_tool_executor_node)  # type: ignore 