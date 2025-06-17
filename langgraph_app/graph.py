# langgraph_app/graph.py

from typing_extensions import TypedDict
from typing import Optional, Dict, Any
import pandas as pd
from langgraph.graph import StateGraph, END

# 🧠 Nodes (Logic Components)
from langgraph_app.nodes.rewrite_agent_node import rewrite_agent_node
from langgraph_app.nodes.tool_executor_node import tool_executor_node
from langgraph_app.nodes.retrieve_memory_node import retrieve_memory_node

# 🔁 Agent Memory + Tool Execution State
class ExpenseAgentState(TypedDict):
    query: str
    tool_input: Optional[Dict[str, Any]]
    result: Optional[str]
    invoked_tool: Optional[str]
    df: pd.DataFrame  # ✅ Ensure DataFrame is passed across the pipeline
    memory: Optional[list[Dict[str, Any]]]  # ✅ Memory for follow-up reasoning
    # Note: No need to add per-tool fields — handled via dynamic tool registry


# 🧩 Create the LangGraph StateGraph
graph = StateGraph(ExpenseAgentState)

# 🔗 Add Nodes
graph.add_node("rewrite_query", rewrite_agent_node)
graph.add_node("retrieve_memory", retrieve_memory_node)
graph.add_node("execute_tool", tool_executor_node)

# 🔀 Define Graph Flow
graph.set_entry_point("rewrite_query")
graph.add_edge("rewrite_query", "retrieve_memory")
graph.add_edge("retrieve_memory", "execute_tool")
graph.add_edge("execute_tool", END)

# 🚀 Compile Graph
expense_analysis_app = graph.compile()
