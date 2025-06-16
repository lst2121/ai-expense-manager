# tools/monthly_expenses_tool.py
from typing_extensions import TypedDict
from typing import Optional
import pandas as pd
from langchain_core.tools import tool
from tools.utils import fuzzy_match_category, parse_month_string

# --- Input Schema ---
class MonthlyExpensesInput(TypedDict):
    df: pd.DataFrame
    month: str
    category: Optional[str]

# --- Main Tool ---
@tool
def monthly_expenses_tool(
    df: pd.DataFrame,
    month: str,
    category: Optional[str] = None
) -> str:
    """
    📆 Monthly Expenses Tool

    Lists all expenses for a given month.
    Optionally filters by category.

    Parameters:
    - df (pd.DataFrame): Your expense sheet (must have 'Amount', 'Date', 'Category', 'Notes')
    - month (str): Month to filter (e.g., 'June 2025', '06/25', '2025-06')
    - category (str, optional): Category to filter (e.g., 'Rent', 'Groceries')

    Returns:
    - str: Formatted expense list or warning/error message
    """
    try:
        filtered = df.copy()

        # --- Month Filter ---
        parsed = parse_month_string(month)
        if not parsed:
            return f"⚠️ Could not parse month from '{month}'"
         # Ensure 'Date' column is string type
        filtered["Date"] = filtered["Date"].astype(str)
        filtered = filtered[filtered["Date"].str.startswith(parsed)]

        # --- Category Filter ---
        matched = None
        if category:
            matched = fuzzy_match_category(category, filtered["Category"].unique().tolist())
            if not matched:
                return f"⚠️ No matching category found for '{category}'"
            filtered = filtered[filtered["Category"] == matched]

        if filtered.empty:
            return f"⚠️ No expenses found for {parsed}{' in category ' + matched if matched else ''}."

        result_lines = [
            f"- {row['Date']} | {row['Category']} | ₹{row['Amount']} | {row['Notes']}"
            for _, row in filtered.iterrows()
        ]
        total = filtered["Amount"].sum()

        title = f"📆 Expenses in {parsed}"
        if matched:
            title += f" (Category: {matched})"

        return f"{title}:\n" + "\n".join(result_lines) + f"\n\n💰 Total: ₹{total:.2f}"

    except Exception as e:
        return f"❌ Error: {str(e)}"
