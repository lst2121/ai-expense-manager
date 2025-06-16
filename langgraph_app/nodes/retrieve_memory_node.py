# langgraph_app/nodes/retrieve_memory_node.py

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
import difflib

def retrieve_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🧠 Retrieve Memory Node

    If tool_input is missing optional context like "category" or "month",
    try resolving it using similar past queries from memory.
    """
    tool_input = state.get("tool_input")
    memory = state.get("memory", [])
    query = state.get("query", "").lower()

    if not tool_input or "arguments" not in tool_input or "tool_name" not in tool_input:
        return state

    args = tool_input["arguments"]
    tool_name = tool_input["tool_name"]

    # ✅ Shortcut: skip if both values already provided
    if all(k in args for k in ["category", "month"]):
        return state

    # 🔁 Try resolving missing parts from memory
    best_match = None
    highest_sim = 0.0
    for past in reversed(memory):
        past_query = past.get("query", "").lower()
        past_args = past.get("tool_args", {}) or {}
        sim = difflib.SequenceMatcher(None, query, past_query).ratio()

        if sim > 0.4 and past.get("tool_name") != "summarize_memory_tool":
            if sim > highest_sim:  # Keep best match
                best_match = past_args
                highest_sim = sim

    # 🧩 Fill missing keys
    if best_match:
        for key in ["category", "month"]:
            if key not in args and key in best_match:
                args[key] = best_match[key]

    # ✅ Update tool_input arguments
    state["tool_input"]["arguments"] = args
    return state

retrieve_memory_node = RunnableLambda(retrieve_memory_node)
