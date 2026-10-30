"""
DuckDB-based Sum Category Expenses Tool
SQL-powered tool for summing expenses by category
"""

import logging
from typing import Dict, Union, Optional
from langchain_core.tools import tool

from ..core.duckdb_manager import DuckDBManager
from ..utils.sql_helpers import SQLQueryBuilder

logger = logging.getLogger(__name__)

@tool
def sum_category_expenses_tool(
    table_name: str = "expenses",
    category: str = "grocery",
    month: Optional[str] = None
) -> Dict[str, Union[str, Optional[str]]]:
    """
    📊 Sum Category Expenses Tool (DuckDB)

    Calculate the total amount spent in a specific category with optional month filtering.
    Uses SQL queries for efficient data processing.

    Parameters
    ----------
    table_name : str
        Name of the expenses table in DuckDB (default: "expenses").
    category : str
        Category to sum expenses for (e.g., "grocery", "food").
    month : str, optional
        Month to filter by. Accepts formats like "2025-01", "June 2025", "last month".

    Returns
    -------
    dict
        A dictionary with:
        - 'text': Formatted summary of total expenses
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
        query = query_builder.build_sum_category_query(
            category=category,
            month=month,
            available_categories=available_categories
        )
        
        logger.debug(f"Executing SQL query: {query}")
        
        # Execute query
        result_df = db_manager.execute_query(query)
        
        # Check if we got results
        if result_df.empty:
            category_msg = f" for category '{category}'" if category else ""
            month_msg = f" in {month}" if month else ""
            return {
                "text": f"🔍 No expenses found{category_msg}{month_msg}.",
                "chart": None
            }
        
        # Extract results
        total_amount = result_df["total_amount"].iloc[0]
        transaction_count = result_df["transaction_count"].iloc[0]
        matched_category = result_df["Category"].iloc[0]
        
        # Build response text
        response_parts = [f"💰 Total spent in '{matched_category}': ₹{total_amount:.2f}"]
        response_parts.append(f"📊 Number of transactions: {transaction_count}")
        
        if month:
            response_parts.append(f"📅 Period: {month}")
        
        response_text = "\n".join(response_parts)
        
        return {
            "text": response_text,
            "chart": None
        }
        
    except Exception as e:
        logger.error(f"Error in sum_category_expenses_tool: {e}")
        return {
            "text": f"❌ Error: {str(e)}",
            "chart": None
        }
    finally:
        # Clean up database connection
        if 'db_manager' in locals():
            db_manager.close() 