from typing import Optional
from typing_extensions import TypedDict
import pandas as pd
from langchain_core.tools import tool
from tools.utils import fuzzy_match_category, parse_month_string
from difflib import get_close_matches
import calendar
import re

# --- Step 1: Input Schema ---
class TopExpensesInput(TypedDict):
    df: pd.DataFrame
    n: int
    category: Optional[str]
    month: Optional[str]
# --- Step 2: Main Tool ---
@tool
def top_expenses_tool(
    df: pd.DataFrame,
    n: int = 3,
    category: Optional[str] = None,
    month: Optional[str] = None
) -> str:
    """
    📊 Top Expenses Tool

    Finds top N highest expenses in a DataFrame.
    Optionally filters by category and/or month.

    Parameters:
    - df (pd.DataFrame): Your expense sheet (must have 'Amount', 'Date', 'Category', 'Notes')
    - n (int): Number of top expenses to return (default: 3)
    - category (str, optional): Category to filter (e.g., 'Groceries', fuzzy matched)
    - month (str, optional): Month to filter (e.g., 'June 2025', '06/25', '2025-06')

    Returns:
    - str: Formatted top-N result string or error/warning
    """
    try:
        filtered = df.copy()

        # --- Category ---
        matched = None
        if category:
            matched = fuzzy_match_category(category, df["Category"].unique().tolist())
            if not matched:
                return f"⚠️ No matching category found for '{category}'"
            filtered = filtered[filtered["Category"] == matched]

        # --- Month ---
        parsed = None
        if month:
            parsed = parse_month_string(month)
            if not parsed:
                return f"⚠️ Could not parse month from '{month}'"
            filtered = filtered[filtered["Date"].str.startswith(parsed)]

        # --- Top N ---
        top_exp = filtered.nlargest(n, "Amount")
        if top_exp.empty:
            return "⚠️ No matching expenses found."

        lines = [
            f"{i+1}. {row['Notes']} - ₹{row['Amount']} ({row['Date']})"
            for i, row in top_exp.reset_index(drop=True).iterrows()
        ]
        total = top_exp["Amount"].sum()

        response = f"Top {n} expenses"
        if matched:
            response += f" in category '{matched}'"
        if parsed:
            response += f" for {parsed}"

        return f"{response}:\n\n" + "\n".join(lines) + f"\n\n💰 Total: ₹{total:.2f}"

    except Exception as e:
        return f"❌ Error: {str(e)}"
