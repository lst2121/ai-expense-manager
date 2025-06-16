from typing import TypedDict, Optional
import pandas as pd
from langchain_core.tools import tool
from tools.utils import parse_month_string, fuzzy_match_category

# --- Input Schema ---
class CompareMonthsInput(TypedDict):
    df: pd.DataFrame
    month1: str
    month2: str
    category: Optional[str]

@tool
def compare_months_tool(
    df: pd.DataFrame,
    month1: str,
    month2: str,
    category: Optional[str] = None
) -> str:
    """
    📊 Compare Months Tool

    Compares expenses between two months (optionally filtered by category).
    Accepts flexible month formats like "June 2025", "2025-06", etc.
    """

    try:
        m1 = parse_month_string(month1)
        m2 = parse_month_string(month2)
        if not m1 or not m2:
            return f"⚠️ Could not parse one of the months: '{month1}', '{month2}'"

        df["Date"] = df["Date"].astype(str)

        df1 = df[df["Date"].str.startswith(m1)]
        df2 = df[df["Date"].str.startswith(m2)]

        cat_label = ""
        if category:
            matched = fuzzy_match_category(category, df["Category"].unique().tolist())
            if not matched:
                return f"⚠️ No matching category found for '{category}'"
            df1 = df1[df1["Category"] == matched]
            df2 = df2[df2["Category"] == matched]
            cat_label = f" in category '{matched}'"

        total1 = df1["Amount"].sum()
        total2 = df2["Amount"].sum()
        delta = total2 - total1

        trend = "📈 increase" if delta > 0 else "📉 decrease" if delta < 0 else "➖ no change"

        summary = f"📊 Comparison of {m1} vs {m2}{cat_label}:\n"
        summary += f"• {m1}: ₹{total1:.2f}\n"
        summary += f"• {m2}: ₹{total2:.2f}\n"
        summary += f"• Difference: ₹{abs(delta):.2f} → {trend}\n"

        return summary

    except Exception as e:
        return f"❌ Error in compare_months_tool: {str(e)}"
