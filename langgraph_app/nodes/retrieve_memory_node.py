# langgraph_app/nodes/retrieve_memory_node.py

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
import difflib

def retrieve_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🧠 Retrieve Memory Node

    If the tool_input is missing required info (e.g. category or month),
    tries to resolve it from memory using recent related queries.
    """
    tool_input = state.get("tool_input")
    memory = state.get("memory", [])
    query = state.get("query", "").lower()

    # If tool input is fine, skip this node
    if not tool_input or "arguments" not in tool_input:
        return state

    args = tool_input["arguments"]
    tool_name = tool_input["tool_name"]

    # Shortcut: if nothing is missing, skip
    if all(k in args for k in ["category", "month"]):
        return state

    # Try to backfill category/month from memory
    best_match = None
    for past in reversed(memory):
        past_args = past.get("tool_args", {})
        past_query = past.get("query", "").lower()
        sim = difflib.SequenceMatcher(None, query, past_query).ratio()

        if sim > 0.4 and past.get("tool_name") != "summarize_memory_tool":
            best_match = past_args
            break

    if best_match:
        # Fill in missing parts
        for key in ["category", "month"]:
            if key not in args and key in best_match:
                args[key] = best_match[key]

    # Update tool_input
    state["tool_input"]["arguments"] = args
    return state

retrieve_memory_node = RunnableLambda(retrieve_memory_node)
