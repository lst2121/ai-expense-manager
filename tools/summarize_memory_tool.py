from typing import List, Dict, Any, Optional, Union
from langchain_core.tools import tool
import pandas as pd
import re

@tool
def summarize_memory_tool(
    memory: Optional[List[Dict[str, Any]]] = None,
    df: Optional[pd.DataFrame] = None
) -> str:
    """
    🧠 Summarize Memory Tool (Enhanced)

    Summarizes total spending and top categories either from:
    - In-memory query history (`memory`)
    - Directly provided `df` with 'Amount', 'Category', 'Date' columns

    Parameters:
    - memory (list): List of tool invocation records with past results (optional)
    - df (pd.DataFrame): Optional DataFrame to summarize directly (skips memory parsing)

    Returns:
    - str: Spending summary
    """
    try:
        records = []

        # ✅ Case 1: Use provided DataFrame
        if df is not None:
            if df.empty or not all(col in df.columns for col in ["Amount", "Category", "Date"]):
                return "⚠️ Provided DataFrame is invalid or empty."

            df = df.copy()
            df["amount"] = df["Amount"]
            df["category"] = df["Category"].fillna("Unknown")
            df["month"] = df["Date"].str[:7]
            records = df[["amount", "category", "month"]].to_dict(orient="records")

        # ✅ Case 2: Parse from memory if no df provided
        elif memory:
            for entry in memory:
                if entry.get("tool_name") == "summarize_memory_tool":
                    continue  # Skip self-references

                args = entry.get("tool_args", {})
                month = args.get("month", "Any") or "Any"
                result_text = str(entry.get("result"))

                lines = result_text.splitlines()
                expense_lines = [line for line in lines if "₹" in line and "|" in line]

                for line in expense_lines:
                    try:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) < 3:
                            continue
                        date, category, amount_str = parts[0], parts[1], parts[2]
                        category = category or args.get("category", "Unknown") or "Unknown"
                        amount = float(amount_str.replace("₹", "").replace(",", ""))

                        records.append({
                            "category": category,
                            "month": month,
                            "amount": amount
                        })
                    except Exception:
                        continue
        else:
            return "🧠 No data available: provide either `memory` or `df`."

        # ✅ Proceed if we have valid records
        if not records:
            return "🧠 No valid expenses found to summarize."

        df_summary = pd.DataFrame(records)
        total = df_summary["amount"].sum()
        top_cats = df_summary.groupby("category")["amount"].sum().sort_values(ascending=False)

        summary = f"🧾 Summary of {len(records)} expense records:\n\n"
        summary += f"💰 Total Recorded Spending: ₹{total:.2f}\n\n"
        summary += "🏷️ Top Spending Categories:\n"
        for cat, amt in top_cats.items():
            summary += f"- {cat}: ₹{amt:.2f}\n"

        return summary

    except Exception as e:
        return f"❌ Error during summary: {str(e)}"
