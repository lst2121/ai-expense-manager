from typing import Dict, Any, List
from langchain_core.runnables import RunnableLambda
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr
from expense_manager import config
import json

llm = ChatDeepSeek(
    temperature=config.TEMPERATURE,
    model=config.DEEPSEEK_MODEL_NAME,
    api_key=SecretStr(config.DEEPSEEK_API_KEY or ""),
    base_url=config.BASE_URL
)

PLANNER_SYSTEM_PROMPT = """
You are an AI expense analysis planner. Your job is to break down complex user queries into sequential steps.

Available Operations:
1. "top_n_expenses" - Find top N expenses (optional: category, month, n)
2. "list_month_expenses" - List expenses for a specific month (required: month, optional: category)
3. "sum_category_expenses" - Total spending for a category (required: category)
4. "date_range_expense" - Expenses in date range (required: start_date, end_date, optional: category)
5. "summarize_memory" - Summarize past analysis
6. "compare_months" - Compare two months (required: month1, month2, optional: category)
7. "compare_category" - Compare two categories (required: category1, category2, optional: months)
8. "average_category_expense" - Average spending per month (required: category, optional: months)
9. "category_summary" - Detailed category breakdown (required: category, optional: months)

IMPORTANT: Return ONLY a JSON object with this structure:
{
  "is_multi_step": true/false,
  "steps": [
    {
      "step_number": 1,
      "description": "Human readable description",
      "operation": "operation_name",
      "arguments": {...}
    }
  ],
  "synthesis_instruction": "How to combine results from all steps"
}

For simple queries, set "is_multi_step": false and include only one step.
For complex queries, set "is_multi_step": true and break into logical steps.

Examples:

Simple Query: "How much did I spend on groceries?"
{
  "is_multi_step": false,
  "steps": [
    {
      "step_number": 1,
      "description": "Calculate total grocery spending",
      "operation": "sum_category_expenses",
      "arguments": {"category": "Groceries"}
    }
  ],
  "synthesis_instruction": "Return the total amount"
}

Complex Query: "Show grocery trends over 3 months, then compare to transportation"
{
  "is_multi_step": true,
  "steps": [
    {
      "step_number": 1,
      "description": "Get grocery expenses for May",
      "operation": "list_month_expenses",
      "arguments": {"month": "2025-05", "category": "Groceries"}
    },
    {
      "step_number": 2,
      "description": "Get grocery expenses for June", 
      "operation": "list_month_expenses",
      "arguments": {"month": "2025-06", "category": "Groceries"}
    },
    {
      "step_number": 3,
      "description": "Get grocery expenses for July",
      "operation": "list_month_expenses", 
      "arguments": {"month": "2025-07", "category": "Groceries"}
    },
    {
      "step_number": 4,
      "description": "Compare groceries vs transportation for the same period",
      "operation": "compare_category",
      "arguments": {"category1": "Groceries", "category2": "Transportation", "months": ["2025-05", "2025-06", "2025-07"]}
    }
  ],
  "synthesis_instruction": "Analyze the grocery spending trend across the 3 months, then compare with transportation spending patterns. Identify which category had higher spending and any notable trends."
}
"""

def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Planning node that breaks complex queries into sequential steps.
    """
    query = state.get("query", "")
    if not query:
        return {
            **state,
            "is_multi_step": False,
            "execution_plan": None,
            "result": "❌ Missing query input."
        }
    
    prompt = f"{PLANNER_SYSTEM_PROMPT}\n\nUser Query: {query}\n\nPlanning Response:"
    
    try:
        response = llm.invoke(prompt)
        content = str(response.content if hasattr(response, "content") else response)
        print(f"\n🧠 PLANNER RESPONSE: {content}")
        
        # Strip code block markers if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        plan = json.loads(content)
        
        is_multi_step = plan.get("is_multi_step", False)
        steps = plan.get("steps", [])
        synthesis_instruction = plan.get("synthesis_instruction", "")
        
        if not steps:
            return {
                **state,
                "is_multi_step": False,
                "execution_plan": None,
                "result": "❌ No execution steps generated."
            }
        
        execution_plan = {
            "steps": steps,
            "synthesis_instruction": synthesis_instruction,
            "current_step": 0,
            "step_results": []
        }
        
        print(f"📋 Execution Plan: {len(steps)} steps, Multi-step: {is_multi_step}")
        
        return {
            **state,
            "is_multi_step": is_multi_step,
            "execution_plan": execution_plan
        }
        
    except Exception as e:
        print(f"❌ Planning error: {e}")
        return {
            **state,
            "is_multi_step": False,
            "execution_plan": None,
            "result": f"❌ Planning failed: {e}"
        }

planner_runnable = RunnableLambda(planner_node) 