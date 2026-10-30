# langgraph_app/graph.py

from typing_extensions import TypedDict
from typing import Optional, Dict, Any
import pandas as pd
from langgraph.graph import StateGraph, END

# 🧠 Nodes (Logic Components)
from langgraph_app.nodes.rewrite_agent_node import rewrite_agent_runnable
from langgraph_app.nodes.duckdb_tool_executor_node import duckdb_tool_executor_node
from langgraph_app.nodes.retrieve_memory_node import retrieve_memory_node
from langgraph_app.nodes.planner_node import planner_runnable
from langgraph_app.nodes.chain_executor_node import chain_executor_runnable

# 🔁 Agent Memory + Tool Execution State
class ExpenseAgentState(TypedDict):
    query: str
    tool_input: Optional[Dict[str, Any]]
    result: Optional[str]
    chart: Optional[str]  # 🚀 NEW: Base64 chart data
    invoked_tool: Optional[str]
    df: pd.DataFrame  # ✅ Ensure DataFrame is passed across the pipeline
    memory: Optional[list[Dict[str, Any]]]  # ✅ Memory for follow-up reasoning
    # 🔄 Multi-step execution fields
    is_multi_step: Optional[bool]  # Whether query requires multi-step processing
    execution_plan: Optional[Dict[str, Any]]  # Step-by-step execution plan
    step_results: Optional[list[Dict[str, Any]]]  # Results from each step


# 🧩 Routing Logic for Multi-step vs Single-step
def route_execution(state: ExpenseAgentState) -> str:
    """Route to either single-step or multi-step execution based on planner decision."""
    is_multi_step = state.get("is_multi_step", False)
    execution_plan = state.get("execution_plan")
    
    # If planning failed or no execution plan, try single-step approach
    if execution_plan is None:
        print("📍 Routing to single-step execution (no plan)")
        return "rewrite_query"
    
    # Route based on complexity
    if is_multi_step:
        print("📍 Routing to multi-step execution")
        return "chain_executor"
    else:
        print("📍 Routing to single-step execution")
        return "rewrite_query"

# 🧩 Create the LangGraph StateGraph
graph = StateGraph(ExpenseAgentState)

# 🔗 Add Nodes
graph.add_node("planner", planner_runnable)
graph.add_node("rewrite_query", rewrite_agent_runnable)
graph.add_node("retrieve_memory", retrieve_memory_node)
graph.add_node("execute_tool", duckdb_tool_executor_node)  # 🚀 Updated to use DuckDB executor
graph.add_node("chain_executor", chain_executor_runnable)

# 🔀 Define Graph Flow
graph.set_entry_point("planner")

# Route from planner to appropriate execution path
graph.add_conditional_edges(
    "planner",
    route_execution,
    {
        "rewrite_query": "rewrite_query",
        "chain_executor": "chain_executor"
    }
)

# Single-step execution path
graph.add_edge("rewrite_query", "retrieve_memory")
graph.add_edge("retrieve_memory", "execute_tool")
graph.add_edge("execute_tool", END)

# Multi-step execution path (direct to end)
graph.add_edge("chain_executor", END)

# 🚀 Compile Graph
expense_analysis_app = graph.compile()
