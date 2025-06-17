# tools/compare_months_tool.py

from typing_extensions import TypedDict
from typing import Optional
import pandas as pd
from langchain_core.tools import tool
from tools.utils import parse_month_string, fuzzy_match_category

# --- Input Schema ---
class CompareMonthsInput(TypedDict):
    df: pd.DataFrame
    month1: str
    month2: str
    category: Optional[str]

# --- Main Tool ---
@tool
def compare_months_tool(
    df: pd.DataFrame,
    month1: str,
    month2: str,
    category: Optional[str] = None
) -> str:
    """
    📊 Compare Months Tool

    Compares total spending between two months.
    Optionally filters by category.

    Parameters:
    - df (pd.DataFrame)
    - month1 (str): e.g. "2025-05"
    - month2 (str): e.g. "2025-06"
    - category (str, optional)

    Returns:
    - str: Text summary of comparison
    """
    try:
        parsed1 = parse_month_string(month1)
        parsed2 = parse_month_string(month2)

        if not parsed1 or not parsed2:
            return "⚠️ Could not parse one of the months."

        data = df.copy()
        data["Date"] = data["Date"].astype(str)

        # Optional category filtering
        matched = None
        if category:
            matched = fuzzy_match_category(category, data["Category"].unique().tolist())
            if not matched:
                return f"⚠️ No matching category found for '{category}'"
            data = data[data["Category"] == matched]

        # Compare totals
        sum1 = data[data["Date"].str.startswith(parsed1)]["Amount"].sum()
        sum2 = data[data["Date"].str.startswith(parsed2)]["Amount"].sum()
        diff = sum2 - sum1
        trend = "📈 increase" if diff > 0 else "📉 decrease" if diff < 0 else "➖ no change"

        title = f"📊 Comparison of {parsed1} vs {parsed2}"
        if matched:
            title += f" in category '{matched}'"

        return (
            f"{title}:\n"
            f"• {parsed1}: ₹{sum1:.2f}\n"
            f"• {parsed2}: ₹{sum2:.2f}\n"
            f"• Difference: ₹{abs(diff):.2f} → {trend}"
        )

    except Exception as e:
        return f"❌ Error: {str(e)}"
