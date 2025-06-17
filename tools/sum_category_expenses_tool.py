# sum_category_expenses_tool.py
from langchain_core.tools import tool
import pandas as pd

@tool
def sum_category_expenses_tool(df: pd.DataFrame, category: str) -> str:
    """Sums total expenses in a given category."""
    filtered_df = df[df['Category'].str.lower().str.rstrip('s') == category.lower().rstrip('s')]

    if filtered_df.empty:
        return f"📂 No expenses found in category '{category}'."
    
    total = filtered_df['Amount'].sum()
    return f"🧾 Total spent on '{category}': ₹{total:.2f}"
