"""
DuckDB-based Top Expenses Tool
SQL-powered tool for finding top N expenses with interactive charts
"""

import logging
from typing import Dict, Union, Optional
from langchain_core.tools import tool

from ..core.duckdb_manager import DuckDBManager
from ..core.chart_generator import PlotlyChartGenerator
from ..utils.sql_helpers import SQLQueryBuilder

logger = logging.getLogger(__name__)

@tool
def top_expenses_tool(
    table_name: str = "expenses",
    n: int = 3,
    category: Optional[str] = None,
    month: Optional[str] = None
) -> Dict[str, Union[str, Optional[str]]]:
    """
    📊 Top Expenses Tool (DuckDB)

    Find the top N highest expenses with optional filters for category and month.
    Generates both a text summary and an interactive horizontal bar chart.

    Parameters
    ----------
    table_name : str
        Name of the expenses table in DuckDB (default: "expenses").
    n : int
        Number of top expenses to return (default: 3).
    category : str, optional
        Category to filter by (e.g., "grocery", "food").
    month : str, optional
        Month to filter by. Accepts formats like "2025-01", "June 2025", "last month".

    Returns
    -------
    dict
        A dictionary with:
        - 'text': Formatted summary of top expenses
        - 'chart': Base64 PNG image string of horizontal bar chart
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
        query = query_builder.build_top_expenses_query(
            n=n,
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
        
        # Build response text
        lines = []
        total_amount = 0
        
        for i, row in result_df.iterrows():
            rank = row['rank']
            notes = row['Notes']
            amount = row['Amount']
            date = row['Date']
            category_name = row['Category']
            
            lines.append(f"{rank}. {notes} - ₹{amount:.2f} ({date})")
            total_amount += amount
        
        # Create summary text
        summary = f"Top {n} expenses"
        if category:
            summary += f" in category '{category}'"
        if month:
            summary += f" for {month}"
        
        summary_text = f"{summary}:\n\n" + "\n".join(lines) + f"\n\n💰 Total: ₹{total_amount:.2f}"
        
        # Generate chart
        chart_title = f"Top {n} Expenses"
        if category:
            chart_title += f" - {category}"
        if month:
            chart_title += f" ({month})"
        
        chart_base64 = chart_generator.create_horizontal_bar_chart(
            df=result_df,
            x_col="Amount",
            y_col="Notes",
            title=chart_title,
            limit=n
        )
        
        return {
            "text": summary_text,
            "chart": chart_base64
        }
        
    except Exception as e:
        logger.error(f"Error in top_expenses_tool: {e}")
        return {
            "text": f"❌ Error: {str(e)}",
            "chart": None
        }
    finally:
        # Clean up database connection
        if 'db_manager' in locals():
            db_manager.close() 