"""
DuckDB-based Category Summary Tool
SQL-powered tool for category analysis with optional charts
"""

import logging
from typing import Dict, Union, Optional
from langchain_core.tools import tool

from ..core.duckdb_manager import DuckDBManager
from ..core.chart_generator import PlotlyChartGenerator
from ..utils.sql_helpers import SQLQueryBuilder
from ..utils.date_utils import DateUtils

logger = logging.getLogger(__name__)

@tool
def category_summary_tool(
    table_name: str = "expenses",
    category: str = "grocery",
    mode: str = "total",
    month: Optional[str] = None
) -> Dict[str, Union[str, Optional[str]]]:
    """
    📊 Category Summary Tool (DuckDB)

    Analyze expenses by category with different modes: total, average, or count.
    Supports fuzzy category matching and optional month filtering.
    Generates text summary and optional charts for visualization.

    Parameters
    ----------
    table_name : str
        Name of the expenses table in DuckDB (default: "expenses").
    category : str
        Category to analyze (e.g., "grocery", "food").
    mode : str
        Analysis mode: "total", "average", or "count".
    month : str, optional
        Month to filter by. Accepts formats like "2025-01", "June 2025", "last month".

    Returns
    -------
    dict
        A dictionary with:
        - 'text': Formatted summary of category analysis
        - 'chart': Base64 PNG image string (for some modes) or None
    """
    try:
        # Initialize DuckDB manager and chart generator
        db_manager = DuckDBManager()
        chart_generator = PlotlyChartGenerator()
        
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
        query = query_builder.build_category_summary_query(
            category=category,
            mode=mode,
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
        matched_category = result_df["Category"].iloc[0]
        result_value = result_df["result_value"].iloc[0]
        transaction_count = result_df["transaction_count"].iloc[0]
        
        # Build response text
        response_parts = [f"📊 {mode.capitalize()} for category '{matched_category}'"]
        
        if month:
            response_parts.append(f" in {month}")
        
        response_parts.append(":")
        
        if mode == "total":
            response_parts.append(f"• Total: ₹{result_value:.2f}")
        elif mode == "average":
            response_parts.append(f"• Average per transaction: ₹{result_value:.2f}")
        elif mode == "count":
            response_parts.append(f"• Transactions: {int(result_value)}")
        
        response_parts.append(f"• Number of transactions: {transaction_count}")
        
        response_text = "\n".join(response_parts)
        
        # Generate chart for certain modes
        chart_base64 = None
        if mode in ["total", "average"] and not result_df.empty:
            # For total/average modes, create a bar chart
            chart_title = f"{mode.capitalize()} for {matched_category}"
            if month:
                chart_title += f" ({month})"
            
            chart_base64 = chart_generator.create_bar_chart(
                df=result_df,
                x_col="Category",
                y_col="result_value",
                title=chart_title
            )
        
        return {
            "text": response_text,
            "chart": chart_base64
        }
        
    except Exception as e:
        logger.error(f"Error in category_summary_tool: {e}")
        return {
            "text": f"❌ Error: {str(e)}",
            "chart": None
        }
    finally:
        # Clean up database connection
        if 'db_manager' in locals():
            db_manager.close() 