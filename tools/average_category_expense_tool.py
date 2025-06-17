# tools/average_category_expense_tool.py

from typing_extensions import TypedDict
from typing import Optional, List, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from langchain_core.tools import tool
from tools.utils import parse_month_string, fuzzy_match_category

# --- Input Schema ---
class AverageCategoryInput(TypedDict):
    df: pd.DataFrame
    category: str
    months: Optional[List[str]]

# --- Helper: Encode chart to base64 ---
def encode_chart_to_base64(fig) -> str:
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64

# --- Main Tool ---
@tool
def average_category_expense_tool(
    df: pd.DataFrame,
    category: str,
    months: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    📈 Average Category Expense Tool

    Calculates the average monthly expense for a given category.
    Optionally filters by selected months.

    Parameters:
    - df (pd.DataFrame): Expense data
    - category (str): Category to analyze
    - months (List[str], optional): List of 'YYYY-MM' strings

    Returns:
    - Dict with:
        • 'text': Summary of average expenses
        • 'chart': base64-encoded bar chart
    """
    try:
        data = df.copy()
        data["Date"] = data["Date"].astype(str)
        data["Month"] = data["Date"].str.slice(0, 7)

        # Fuzzy match category
        matched_category = fuzzy_match_category(category, data["Category"].unique().tolist())
        if not matched_category:
            return {
                "text": f"⚠️ Could not match category '{category}'",
                "chart": None
            }

        # Filter by category
        data = data[data["Category"].str.lower() == matched_category.lower()]

        # Filter months if provided
        if months:
            parsed_months = [parse_month_string(m) for m in months]
            parsed_months = [m for m in parsed_months if m]
            if not parsed_months:
                return {
                    "text": "⚠️ No valid months provided.",
                    "chart": None
                }
            data = data[data["Month"].isin(parsed_months)]

        if data.empty:
            return {
                "text": f"⚠️ No data found for '{matched_category}' in selected months.",
                "chart": None
            }

        # Group and calculate average
        avg_monthly = data.groupby("Month")["Amount"].mean().sort_index()

        # --- Plot chart ---
        fig, ax = plt.subplots(figsize=(8, 4))
        avg_monthly.plot(kind="bar", color="teal", ax=ax)
        ax.set_title(f"Average {matched_category} Expense by Month")
        ax.set_ylabel("Avg Amount (₹)")
        ax.set_xlabel("Month")
        ax.grid(True, linestyle="--", alpha=0.6)
        fig.tight_layout()
        chart = encode_chart_to_base64(fig)

        # --- Summary text ---
        summary = f"📈 Average expense per month for '{matched_category}':\n"
        for month, amt in avg_monthly.items():
            summary += f"• {month}: ₹{amt:.2f}\n"

        return {
            "text": summary.strip(),
            "chart": chart
        }

    except Exception as e:
        return {
            "text": f"❌ Error: {str(e)}",
            "chart": None
        }
