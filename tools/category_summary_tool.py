from typing import Dict, Any, Optional
import pandas as pd
from langchain_core.tools import tool
from tools.utils import resolve_time_period, fuzzy_match_category

@tool
def category_summary_tool(
    df: pd.DataFrame,
    category: str,
    mode: str = "total",
    month: Optional[str] = None
) -> Dict[str, Any]:
    """
    📊 Category Summary Tool

    Supports modes:
    • total → Total spent in the category
    • average → Monthly average
    • count → Number of transactions

    Optional: filter by fuzzy category and month.

    Parameters:
    - df (pd.DataFrame): Expense data
    - category (str): Category to summarize
    - mode (str): total | average | count
    - month (str, optional): e.g., 'last month', '2025-06'

    Returns:
    - dict: {'text': ..., 'chart': None}
    """
    try:
        if df.empty:
            return {
                "text": "⚠️ No data available to analyze.",
                "chart": None
            }

        data = df.copy()
        data["Date"] = pd.to_datetime(data["Date"])
        data["Month"] = data["Date"].dt.to_period("M").astype(str)

        # Fuzzy match category
        matched_category = fuzzy_match_category(category, data["Category"].unique().tolist())
        if not matched_category:
            return {
                "text": f"❌ Could not match category '{category}'.",
                "chart": None
            }

        data = data[data["Category"].str.lower() == matched_category.lower()]

        # Filter by month if given
        resolved_period_str = ""
        if month:
            resolved = resolve_time_period(month)
            if isinstance(resolved, list):
                data = data[data["Month"].isin(resolved)]
                resolved_period_str = ", ".join(resolved)
            elif isinstance(resolved, str):
                data = data[data["Month"] == resolved]
                resolved_period_str = resolved
            else:
                return {
                    "text": f"❌ Could not resolve time period '{month}'.",
                    "chart": None
                }

        if data.empty:
            return {
                "text": f"🔍 No records found for '{matched_category}'{f' in {resolved_period_str}' if month else ''}.",
                "chart": None
            }

        # Compose result text
        result = f"📊 {mode.capitalize()} for category '{matched_category}'"
        if resolved_period_str:
            result += f" in {resolved_period_str}"
        result += ":\n"

        if mode == "total":
            total = data["Amount"].sum()
            result += f"• Total: ₹{total:.2f}"
        elif mode == "average":
            monthly_avg = data.groupby("Month")["Amount"].sum().mean()
            result += f"• Average per month: ₹{monthly_avg:.2f}"
        elif mode == "count":
            count = len(data)
            result += f"• Transactions: {count}"
        else:
            return {
                "text": f"❌ Invalid mode '{mode}'. Choose from total, average, count.",
                "chart": None
            }

        return {"text": result, "chart": None}

    except Exception as e:
        return {"text": f"❌ Error: {str(e)}", "chart": None}
