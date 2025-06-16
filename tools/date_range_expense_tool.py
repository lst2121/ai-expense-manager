from typing import Optional
from typing_extensions import TypedDict
import pandas as pd
from langchain_core.tools import tool
from tools.utils import fuzzy_match_category

# --- Step 1: Input Schema ---
class DateRangeExpenseInput(TypedDict):
    df: pd.DataFrame
    start_date: str
    end_date: str
    category: Optional[str]

# --- Step 2: Main Tool ---
@tool
def date_range_expense_tool(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
    category: Optional[str] = None,
) -> str:
    """
    📆 Date Range Expense Tool

    Filters expenses between two dates (inclusive), optionally by category.

    Parameters:
    - df (pd.DataFrame): Your expense sheet (must include 'Date', 'Amount', 'Category', 'Notes')
    - start_date (str): Start date in YYYY-MM-DD format
    - end_date (str): End date in YYYY-MM-DD format
    - category (str, optional): Filter by category (fuzzy matched)

    Returns:
    - str: Summary of matching expenses and total amount
    """
    try:
        filtered = df.copy()
        filtered["Date"] = pd.to_datetime(filtered["Date"])

        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        filtered = filtered[(filtered["Date"] >= start) & (filtered["Date"] <= end)]

        matched = None
        if category:
            matched = fuzzy_match_category(category, df["Category"].unique().tolist())
            if not matched:
                return f"⚠️ No matching category found for '{category}'"
            filtered = filtered[filtered["Category"] == matched]

        if filtered.empty:
            msg = f"No expenses found from {start_date} to {end_date}"
            if category:
                msg += f" in category '{category}'."
            return f"⚠️ {msg}"

        total = filtered["Amount"].sum()
        lines = [
            f"- {row['Date'].date()} | {row['Category']} | ₹{row['Amount']} | {row['Notes']}"
            for _, row in filtered.iterrows()
        ]

        title = f"🗓️ Expenses from {start_date} to {end_date}"
        if matched:
            title += f" in category '{matched}'"

        return f"{title}:\n\n" + "\n".join(lines) + f"\n\n💰 Total: ₹{total:.2f}"

    except Exception as e:
        return f"❌ Error: {str(e)}"
