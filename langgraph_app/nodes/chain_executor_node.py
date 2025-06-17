from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr
from expense_manager import config
from tools.utils import resolve_time_period
import json

# Import all tools
from tools.top_expenses_tool import top_expenses_tool
from tools.monthly_expenses_tool import monthly_expenses_tool
from tools.sum_category_expenses_tool import sum_category_expenses_tool
from tools.date_range_expense_tool import date_range_expense_tool
from tools.summarize_memory_tool import summarize_memory_tool
from tools.compare_months_tool import compare_months_tool
from tools.compare_category_tool import compare_category_tool
from tools.average_category_expense_tool import average_category_expense_tool
from tools.category_summary_tool import category_summary_tool

llm = ChatDeepSeek(
    temperature=config.TEMPERATURE,
    model=config.DEEPSEEK_MODEL_NAME,
    api_key=SecretStr(config.DEEPSEEK_API_KEY or ""),
    base_url=config.BASE_URL
)

# Tool registry for execution
TOOL_REGISTRY = {
    "top_n_expenses": top_expenses_tool,
    "list_month_expenses": monthly_expenses_tool,
    "sum_category_expenses": sum_category_expenses_tool,
    "date_range_expense": date_range_expense_tool,
    "summarize_memory": summarize_memory_tool,
    "compare_months": compare_months_tool,
    "compare_category": compare_category_tool,
    "average_category_expense": average_category_expense_tool,
    "category_summary": category_summary_tool,
}

SYNTHESIS_SYSTEM_PROMPT = """
You are an AI assistant that synthesizes results from multiple analysis steps into a coherent, comprehensive response.

You will receive:
1. The original user query
2. Multiple step results from expense analysis tools
3. Instructions on how to synthesize the results

Create a comprehensive, well-formatted response that:
- Answers the original question completely
- Combines insights from all steps
- Uses clear formatting with emojis and bullet points
- Highlights key findings and trends
- Provides actionable insights where possible

Keep the response conversational but informative.
"""

def execute_single_step(step: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single step and return the result."""
    operation = step.get("operation")
    arguments = step.get("arguments", {})
    description = step.get("description", "")
    
    if operation not in TOOL_REGISTRY:
        return {
            "success": False,
            "result": f"❌ Unknown operation: {operation}",
            "step_description": description
        }
    
    try:
        # Prepare arguments
        tool_args = arguments.copy()
        
        # Add DataFrame if tool needs it
        if operation != "summarize_memory":
            tool_args["df"] = state.get("df")
        
        # Add memory if needed
        if operation == "summarize_memory":
            tool_args["memory"] = state.get("memory", [])
        
        # Resolve time periods
        time_keys = []
        if operation == "list_month_expenses":
            time_keys = ["month"]
        elif operation in ["compare_category", "average_category_expense", "category_summary"]:
            time_keys = ["months"]
        elif operation == "compare_months":
            time_keys = ["month1", "month2"]
        
        for key in time_keys:
            if key in tool_args and tool_args[key]:
                if isinstance(tool_args[key], list):
                    resolved_list = []
                    for val in tool_args[key]:
                        resolved = resolve_time_period(val)
                        if resolved:
                            if isinstance(resolved, list):
                                resolved_list.extend(resolved)
                            else:
                                resolved_list.append(resolved)
                    tool_args[key] = resolved_list
                else:
                    resolved = resolve_time_period(tool_args[key])
                    if resolved:
                        tool_args[key] = resolved
        
        print(f"⚙️ Executing Step: {description}")
        print(f"📦 Tool: {operation}")
        print(f"📥 Args: {tool_args}")
        
        # Execute tool
        tool = TOOL_REGISTRY[operation]
        result = tool.invoke(tool_args)
        
        # Extract text result
        text_result = result.get("text", result) if isinstance(result, dict) else result
        
        return {
            "success": True,
            "result": text_result,
            "step_description": description,
            "operation": operation,
            "arguments": arguments
        }
        
    except Exception as e:
        return {
            "success": False,
            "result": f"❌ Step execution failed: {e}",
            "step_description": description
        }

def synthesize_results(query: str, step_results: list, synthesis_instruction: str) -> str:
    """Synthesize multiple step results into a comprehensive response."""
    try:
        # Prepare the synthesis prompt
        results_text = ""
        for i, step_result in enumerate(step_results, 1):
            if step_result["success"]:
                results_text += f"\n**Step {i} ({step_result['step_description']}):**\n{step_result['result']}\n"
            else:
                results_text += f"\n**Step {i} FAILED ({step_result['step_description']}):**\n{step_result['result']}\n"
        
        prompt = f"""
{SYNTHESIS_SYSTEM_PROMPT}

Original Query: {query}

Step Results:
{results_text}

Synthesis Instructions: {synthesis_instruction}

Please provide a comprehensive response:
"""
        
        response = llm.invoke(prompt)
        content = str(response.content if hasattr(response, "content") else response)
        
        return content.strip()
        
    except Exception as e:
        return f"❌ Failed to synthesize results: {e}\n\nRaw results:\n{results_text}"

def chain_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a chain of steps and synthesize the results.
    """
    execution_plan = state.get("execution_plan")
    if not execution_plan:
        return {
            **state,
            "result": "❌ No execution plan available."
        }
    
    steps = execution_plan.get("steps", [])
    synthesis_instruction = execution_plan.get("synthesis_instruction", "")
    query = state.get("query", "")
    
    if not steps:
        return {
            **state,
            "result": "❌ No steps to execute."
        }
    
    print(f"\n🔄 Executing {len(steps)} steps...")
    
    # Execute each step
    step_results = []
    for i, step in enumerate(steps):
        print(f"\n📍 Step {i+1}/{len(steps)}: {step.get('description', 'Unknown step')}")
        step_result = execute_single_step(step, state)
        step_results.append(step_result)
        
        # Stop if a critical step fails
        if not step_result["success"] and "required" in step.get("description", "").lower():
            break
    
    # Update memory with all successful steps
    memory = state.get("memory", [])
    for step_result in step_results:
        if step_result["success"]:
            memory_entry = {
                "query": f"{query} (Step: {step_result['step_description']})",
                "tool_name": f"{step_result['operation']}_tool",
                "tool_args": {k: v for k, v in step_result.get("arguments", {}).items() if k not in ["df", "memory"]},
                "answer": step_result["result"]
            }
            memory.append(memory_entry)
    
    # Synthesize results if multiple steps
    if len(steps) > 1:
        print(f"\n🧠 Synthesizing {len(step_results)} step results...")
        final_result = synthesize_results(query, step_results, synthesis_instruction)
    else:
        # Single step - return result directly
        final_result = step_results[0]["result"] if step_results and step_results[0]["success"] else "❌ Step execution failed."
    
    return {
        **state,
        "result": final_result,
        "memory": memory,
        "step_results": step_results
    }

chain_executor_runnable = RunnableLambda(chain_executor_node) 