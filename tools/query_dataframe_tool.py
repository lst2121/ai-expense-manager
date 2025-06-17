# query_dataframe_tool.py
from typing import Optional
import pandas as pd
from langchain_core.tools import tool
import difflib
import re
import calendar

# --- Helper: Map natural language month (e.g. "June 2025") to "2025-06"
def parse_month_string(text: str) -> Optional[str]:
    pattern = r"(?i)(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
    match = re.search(pattern, text)
    if match:
        month_name = match.group(1)
        year = match.group(2)
        month_number = list(calendar.month_name).index(month_name.capitalize())
        return f"{year}-{month_number:02d}"
    return text if re.match(r"\d{4}-\d{2}", text) else None

# --- Helper: Fuzzy match category
def fuzzy_match_category(category: str, available_categories: list[str]) -> Optional[str]:
    matches = difflib.get_close_matches(category, available_categories, n=1, cutoff=0.6)
    return matches[0] if matches else None

# --- Main logic
def query_dataframe_tool(
    df: pd.DataFrame,
    operation: str,
    category: Optional[str] = None,
    month: Optional[str] = None,
    n: int = 3
) -> str:
    try:
        df["Category"] = df["Category"].astype(str)
        df["Date"] = df["Date"].astype(str)

        # Normalize month
        if month:
            month = parse_month_string(month)

        # Normalize category with fuzzy match
        all_categories = df["Category"].unique().tolist()
        if category:
            matched = fuzzy_match_category(category.lower(), [c.lower() for c in all_categories])
            if matched:
                actual_category = next(c for c in all_categories if c.lower() == matched)
                category = actual_category
            else:
                return f"⚠️ No matching category found for '{category}'."

        # ---- Operation: Top N Expenses ----
        if operation == "top_n_expenses":
            filtered = df.copy()
            if category:
                filtered = filtered[filtered["Category"].str.lower() == category.lower()]
            if month:
                filtered = filtered[filtered["Date"].str.startswith(month)]

            top_expenses = filtered.nlargest(n, "Amount")
            if top_expenses.empty:
                return f"⚠️ No matching expenses found."

            lines = [
                f"{i+1}. {row['Notes']} - ₹{row['Amount']} ({row['Date']})"
                for i, row in top_expenses.reset_index(drop=True).iterrows()
            ]
            total = top_expenses["Amount"].sum()
            desc = f"Top {n} expenses"
            if category: desc += f" in category '{category}'"
            if month: desc += f" for {month}"
            return f"{desc}:\n\n" + "\n".join(lines) + f"\n\n💰 Total: ₹{total:.2f}"

        # ---- Operation: List Monthly Expenses ----
        elif operation == "list_month_expenses":
            if not month:
                return "❌ 'month' (YYYY-MM or Month YYYY) is required for listing monthly expenses."

            filtered = df[df["Date"].str.startswith(month)]
            if category:
                filtered = filtered[filtered["Category"].str.lower() == category.lower()]

            if filtered.empty:
                return f"⚠️ No expenses found for given filters."

            lines = [
                f"- {row['Date']} | {row['Category']} | ₹{row['Amount']} | {row['Notes']}"
                for _, row in filtered.iterrows()
            ]
            total = filtered["Amount"].sum()
            return f"📆 Expenses in {month}:\n\n" + "\n".join(lines) + f"\n\n💰 Total: ₹{total:.2f}"

        else:
            return f"❌ Unknown operation '{operation}'"

    except Exception as e:
        return f"❌ Error during query: {str(e)}"

# --- LangChain-compatible wrapper ---
@tool
def query_tool(
    df: pd.DataFrame,
    operation: str,
    category: Optional[str] = None,
    month: Optional[str] = None,
    n: int = 3
) -> str:
    """
    Query your expense dataframe.

    Supports:
    - 'top_n_expenses'
    - 'list_month_expenses'

    Optional filters:
    - category: e.g., 'Grocery', 'Rent', etc.
    - month: e.g., '2025-06' or 'June 2025'
    """
    return query_dataframe_tool(df, operation, category, month, n)
