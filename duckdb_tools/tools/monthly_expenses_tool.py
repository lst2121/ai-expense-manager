"""
DuckDB-based Monthly Expenses Tool
SQL-powered tool for listing expenses by month
"""

import logging
from typing import Dict, Union, Optional
from langchain_core.tools import tool

from ..core.duckdb_manager import DuckDBManager
from ..utils.sql_helpers import SQLQueryBuilder

logger = logging.getLogger(__name__)

@tool
def monthly_expenses_tool(
    table_name: str = "expenses",
    month: str = "2025-01",
    category: Optional[str] = None
) -> Dict[str, Union[str, Optional[str]]]:
    """
    📆 Monthly Expenses Tool (DuckDB)

    List all expenses for a given month with optional category filtering.
    Uses SQL queries for efficient data processing.

    Parameters
    ----------
    table_name : str
        Name of the expenses table in DuckDB (default: "expenses").
    month : str
        Month to filter by. Accepts formats like "2025-01", "June 2025", "last month".
    category : str, optional
        Category to filter by (e.g., "grocery", "food").

    Returns
    -------
    dict
        A dictionary with:
        - 'text': Formatted list of expenses
        - 'chart': None (text-only tool)
    """
    try:
        # Initialize DuckDB manager
        db_manager = DuckDBManager()
        
        # Get available categories for fuzzy matching
        table_info = db_manager.get_table_info(table_name)
        available_categories = table_info.get("categories", [])
        
        if not available_categories:
            return {
                "text": "⚠️ No data available to analyze.",
                "chart": None
            }
        
        # Build SQL query
        query_builder = SQLQueryBuilder(table_name)
        query = query_builder.build_monthly_expenses_query(
            month=month,
            category=category,
            available_categories=available_categories
        )
        
        logger.debug(f"Executing SQL query: {query}")
        
        # Execute query
        result_df = db_manager.execute_query(query)
        
        # Check if we got results
        if result_df.empty:
            category_msg = f" in category '{category}'" if category else ""
            return {
                "text": f"🔍 No expenses found for {month}{category_msg}.",
                "chart": None
            }
        
        # Format results
        expense_lines = []
        total_amount = 0
        
        for _, row in result_df.iterrows():
            date_str = row["Date"]
            category_str = row["Category"]
            amount = row["Amount"]
            notes = row.get("Notes", "")
            
            expense_lines.append(f"- {date_str} | {category_str} | ₹{amount:.2f} | {notes}")
            total_amount += amount
        
        # Build response text
        title = f"📆 Expenses in {month}"
        if category:
            title += f" (Category: {category})"
        
        response_parts = [title + ":"]
        response_parts.extend(expense_lines)
        response_parts.append(f"\n💰 Total: ₹{total_amount:.2f}")
        response_parts.append(f"📊 Number of transactions: {len(expense_lines)}")
        
        response_text = "\n".join(response_parts)
        
        return {
            "text": response_text,
            "chart": None
        }
        
    except Exception as e:
        logger.error(f"Error in monthly_expenses_tool: {e}")
        return {
            "text": f"❌ Error: {str(e)}",
            "chart": None
        }
    finally:
        # Clean up database connection
        if 'db_manager' in locals():
            db_manager.close() 