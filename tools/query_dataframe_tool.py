# tools/query_dataframe_tool.py

from typing import Optional
import pandas as pd
from langchain_core.tools import tool

# Core logic function (undecorated)
def query_dataframe_tool(
    df: pd.DataFrame,
    operation: str,
    category: Optional[str] = None,
    month: Optional[str] = None,
    n: int = 3
) -> str:
    """
    Tool to query expense dataframe.

    Parameters:
        df (pd.DataFrame): Your expense dataframe.
        operation (str): One of 'top_n_expenses', 'list_month_expenses'
        category (str): Optional category filter (e.g., 'Groceries')
        month (str): Optional month filter (e.g., '2025-06')
        n (int): For top N expense queries

    Returns:
        str: Result message.
    """

    try:
        if operation == "top_n_expenses":
            filtered_df = df.copy()
            if category:
                filtered_df = filtered_df[filtered_df["Category"].str.lower() == category.lower()]
            if month:
                filtered_df = filtered_df[filtered_df["Date"].str.startswith(month)]

            top_expenses = filtered_df.nlargest(n, "Amount")

            if top_expenses.empty:
                return f"⚠️ No matching expenses found."

            result_lines = [
                f"{i+1}. {row['Notes']} - ₹{row['Amount']} ({row['Date']})"
                for i, row in top_expenses.reset_index(drop=True).iterrows()
            ]
            total = top_expenses["Amount"].sum()

            response = f"Top {n} expenses"
            if category:
                response += f" in category '{category}'"
            if month:
                response += f" for {month}"

            return f"{response}:\n\n" + "\n".join(result_lines) + f"\n\n💰 Total: ₹{total:.2f}"

        elif operation == "list_month_expenses":
            if not month:
                return "❌ 'month' (YYYY-MM) is required for listing monthly expenses."

            filtered = df[df["Date"].str.startswith(month)]

            if filtered.empty:
                return f"⚠️ No expenses found for {month}."

            result_lines = [
                f"- {row['Date']} | {row['Category']} | ₹{row['Amount']} | {row['Notes']}"
                for _, row in filtered.iterrows()
            ]
            total = filtered["Amount"].sum()

            return f"📆 Expenses in {month}:\n\n" + "\n".join(result_lines) + f"\n\n💰 Total: ₹{total:.2f}"

        else:
            return f"❌ Unknown operation '{operation}'"

    except Exception as e:
        return f"❌ Error during query: {str(e)}"


# LangChain-compatible wrapper
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
    - top_n_expenses
    - list_month_expenses

    You can filter by category and/or month (YYYY-MM).
    """
    return query_dataframe_tool(df, operation, category, month, n)
