# langgraph_app/graph.py

from typing_extensions import TypedDict
from typing import Optional, Dict, Any
import pandas as pd
from langgraph.graph import StateGraph, END
from langgraph_app.nodes.rewrite_agent_node import rewrite_agent_node
from langgraph_app.nodes.tool_executor_node import tool_executor_node


class ExpenseAgentState(TypedDict):
    query: str
    tool_input: Optional[Dict[str, Any]]
    result: Optional[str]
    invoked_tool: Optional[str]
    df: pd.DataFrame  # ✅ DataFrame passed through state for all tools
    memory: Optional[list[Dict[str, Any]]]  # ✅ Add this


# Build the graph with 2 nodes: rewriter and tool executor
graph = StateGraph(ExpenseAgentState)

# Add your nodes
graph.add_node("rewrite_query", rewrite_agent_node)
graph.add_node("execute_tool", tool_executor_node)

# Set entry and flow
graph.set_entry_point("rewrite_query")
graph.add_edge("rewrite_query", "execute_tool")
graph.add_edge("execute_tool", END)

# Compile the app
expense_analysis_app = graph.compile()
