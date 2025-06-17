from typing import Optional, Dict, Union
from typing_extensions import TypedDict
import pandas as pd
from langchain_core.tools import tool
from tools.utils import fuzzy_match_category, parse_month_string
import matplotlib.pyplot as plt
import io
import base64

class TopExpensesInput(TypedDict):
    df: pd.DataFrame
    n: int
    category: Optional[str]
    month: Optional[str]

@tool
def top_expenses_tool(
    df: pd.DataFrame,
    n: int = 3,
    category: Optional[str] = None,
    month: Optional[str] = None
) -> Dict[str, Union[str, None]]:
    """
    📊 Top Expenses Tool (Enhanced)

    Find the top N highest expenses with optional filters for category and month.
    Generates both a text summary and a bar chart of the results.

    Parameters
    ----------
    df : pd.DataFrame
        Expense DataFrame with columns: 'Amount', 'Date', 'Category', 'Notes'.
    n : int, optional
        Number of top expenses to return (default is 3).
    category : str, optional
        Fuzzy-matched category to filter by (e.g., "grocery").
    month : str, optional
        Month to filter by. Accepts formats like "2025-06", "June 2025", "06/25".

    Returns
    -------
    dict
        A dictionary with:
        - 'text': Formatted summary of top expenses
        - 'chart': Base64 PNG image string of horizontal bar chart, or None on failure
    """
    try:
        filtered = df.copy()
        
        # Early empty check
        if filtered.empty:
            return {
                "text": "⚠️ No data available to analyze.",
                "chart": None
            }

        # --- Filter by Category ---
        matched_category = None
        if category:
            matched_category = fuzzy_match_category(category, df["Category"].unique().tolist())
            if not matched_category:
                return {
                    "text": f"⚠️ No matching category found for '{category}'",
                    "chart": None
                }
            filtered = filtered[filtered["Category"] == matched_category]

        # --- Filter by Month ---
        parsed_month = None
        if month:
            parsed_month = parse_month_string(month)
            if not parsed_month:
                return {
                    "text": f"⚠️ Could not parse month from '{month}'",
                    "chart": None
                }
            filtered = filtered[filtered["Date"].str.startswith(parsed_month)]

        # --- Get Top N Expenses ---
        top_exp = filtered.nlargest(n, "Amount")
        if top_exp.empty:
            return {
                "text": "⚠️ No matching expenses found.",
                "chart": None
            }

        lines = [
            f"{i+1}. {row['Notes']} - ₹{row['Amount']} ({row['Date']})"
            for i, row in top_exp.reset_index(drop=True).iterrows()
        ]
        total = top_exp["Amount"].sum()
        summary = f"Top {n} expenses"
        if matched_category:
            summary += f" in category '{matched_category}'"
        if parsed_month:
            summary += f" for {parsed_month}"
        summary_text = f"{summary}:\n\n" + "\n".join(lines) + f"\n\n💰 Total: ₹{total:.2f}"

        # --- Create Chart ---
        fig, ax = plt.subplots()
        top_exp_sorted = top_exp.sort_values(by="Amount", ascending=True)
        ax.barh(top_exp_sorted["Notes"], top_exp_sorted["Amount"], color="skyblue")
        ax.set_xlabel("Amount (₹)")
        ax.set_title(f"Top {n} Expenses")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode("utf-8")

        return {
            "text": summary_text,
            "chart": chart_base64
        }

    except Exception as e:
        return {
            "text": f"❌ Error: {str(e)}",
            "chart": None
        }
