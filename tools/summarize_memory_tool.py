from typing import List, Dict, Any
from langchain_core.tools import tool
import pandas as pd
import re

@tool
def summarize_memory_tool(memory: List[Dict[str, Any]]) -> str:
    """
    🧠 Summarize Memory Tool (Enhanced)

    Aggregates past query results from in-memory history.
    Extracts multiple ₹ values and infers categories if missing.
    """
    try:
        if not memory:
            return "🧠 Memory is empty. No spending history to summarize."

        records = []

        for entry in memory:
            if entry.get("tool_name") == "summarize_memory_tool":
                continue  # Skip self-references

            args = entry.get("tool_args", {})
            month = args.get("month", "Any") or "Any"
            result_text = str(entry.get("result"))

            # Extract all lines with actual expenses
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
                        "amount": amount,
                        "query": entry.get("query"),
                        "tool": entry.get("tool_name")
                    })
                except Exception:
                    continue

        if not records:
            return "🧠 No valid expenses found in memory."

        df = pd.DataFrame(records)
        total = df["amount"].sum()
        top_cats = df.groupby("category")["amount"].sum().sort_values(ascending=False)

        summary = f"🧾 Summary of {len(memory)} past queries:\n\n"
        summary += f"💰 Total Recorded Spending: ₹{total:.2f}\n\n"
        summary += "🏷️ Top Spending Categories:\n"
        for cat, amt in top_cats.items():
            summary += f"- {cat}: ₹{amt:.2f}\n"

        return summary

    except Exception as e:
        return f"❌ Error during summary: {str(e)}"
