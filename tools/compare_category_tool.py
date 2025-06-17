# tools/compare_category_tool.py

from typing_extensions import TypedDict
from typing import Optional, List, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from langchain_core.tools import tool
from tools.utils import parse_month_string, fuzzy_match_category

# --- Input Schema ---
class CompareCategoriesInput(TypedDict):
    df: pd.DataFrame
    category1: str
    category2: str
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
def compare_category_tool(
    df: pd.DataFrame,
    category1: str,
    category2: str,
    months: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    📊 Compare Category Tool

    Compares spending between two categories across months.
    Optionally filters by selected months.

    Parameters:
    - df (pd.DataFrame)
    - category1 (str)
    - category2 (str)
    - months (List[str], optional): List of 'YYYY-MM' strings

    Returns:
    - Dict with:
        • 'text': Summary of category comparison
        • 'chart': base64-encoded bar chart
    """
    try:
        data = df.copy()
        data["Date"] = data["Date"].astype(str)

        # Fuzzy match both categories
        cat1 = fuzzy_match_category(category1, data["Category"].unique().tolist())
        cat2 = fuzzy_match_category(category2, data["Category"].unique().tolist())

        if not cat1 or not cat2:
            return {
                "text": f"⚠️ Could not match categories '{category1}' or '{category2}'",
                "chart": None
            }

        # Filter for both categories
        data = data[data["Category"].isin([cat1, cat2])]
        data["Month"] = data["Date"].str.slice(0, 7)

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

        # Pivot for aggregation
        pivot = (
            data.groupby(["Month", "Category"])["Amount"]
            .sum()
            .unstack(fill_value=0)
            .reindex(columns=[cat1, cat2])
        )

        # --- Plot chart ---
        fig, ax = plt.subplots(figsize=(8, 4))
        pivot.plot(kind="bar", ax=ax)
        ax.set_title(f"{cat1} vs {cat2} Spending by Month")
        ax.set_ylabel("Amount (₹)")
        ax.set_xlabel("Month")
        ax.legend(title="Category", loc="upper right")
        fig.tight_layout()
        chart = encode_chart_to_base64(fig)

        # --- Text Summary ---
        total_cat1 = pivot[cat1].sum()
        total_cat2 = pivot[cat2].sum()
        winner = cat1 if total_cat1 > total_cat2 else cat2 if total_cat2 > total_cat1 else "both categories equally"
        summary = (
            f"📊 Comparison of '{cat1}' vs '{cat2}':\n"
            f"• Total {cat1}: ₹{total_cat1:.2f}\n"
            f"• Total {cat2}: ₹{total_cat2:.2f}\n"
            f"• Higher spend: {winner}"
        )

        return {
            "text": summary,
            "chart": chart
        }

    except Exception as e:
        return {
            "text": f"❌ Error: {str(e)}",
            "chart": None
        }
