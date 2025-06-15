# langgraph_app/graph.py

from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph_app.nodes.rewrite_agent_node import rewrite_agent_node
from langgraph_app.nodes.tool_executor_node import tool_executor_node
import pandas as pd

class ExpenseAgentState(TypedDict):
    query: str
    tool_input: Optional[Dict[str, Any]]
    result: Optional[str]
    df: pd.DataFrame  # ✅ New: include df in state

graph = StateGraph(ExpenseAgentState)
graph.add_node("rewrite_query", rewrite_agent_node)
graph.add_node("execute_tool", tool_executor_node)
graph.set_entry_point("rewrite_query")
graph.add_edge("rewrite_query", "execute_tool")
graph.add_edge("execute_tool", END)

expense_analysis_app = graph.compile()
