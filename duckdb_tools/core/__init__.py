"""
Core DuckDB components for expense analysis
"""

from .duckdb_manager import DuckDBManager
from .chart_generator import PlotlyChartGenerator

__all__ = ["DuckDBManager", "PlotlyChartGenerator"] 