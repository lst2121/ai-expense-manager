"""
SQL Query Builder utilities for DuckDB tools
"""

import logging
from typing import Optional, List, Dict
from difflib import get_close_matches

logger = logging.getLogger(__name__)

class SQLQueryBuilder:
    """
    Builds SQL queries for expense analysis
    """
    
    def __init__(self, table_name: str = "expenses"):
        """
        Initialize query builder
        
        Args:
            table_name: Name of the expenses table
        """
        self.table_name = table_name
    
    def build_category_filter(self, category: str, available_categories: List[str]) -> str:
        """
        Build SQL filter for category with fuzzy matching
        
        Args:
            category: Category to filter by
            available_categories: List of available categories
            
        Returns:
            str: SQL WHERE clause for category filter
        """
        if not category:
            return ""
        
        # Fuzzy match category
        matched_category = self._fuzzy_match_category(category, available_categories)
        if not matched_category:
            return ""
        
        return f"AND Category ILIKE '%{matched_category}%'"
    
    def build_date_filter(self, month: str) -> str:
        """
        Build SQL filter for date/month
        
        Args:
            month: Month string (e.g., '2025-01', 'last month')
            
        Returns:
            str: SQL WHERE clause for date filter
        """
        if not month:
            return ""
        
        # Parse month string
        parsed_month = self._parse_month_string(month)
        if not parsed_month:
            return ""
        
        return f"AND Month = '{parsed_month}'"
    
    def build_sum_category_query(
        self, 
        category: str, 
        month: Optional[str] = None,
        available_categories: Optional[List[str]] = None
    ) -> str:
        """
        Build SQL query for summing category expenses
        
        Args:
            category: Category to sum
            month: Optional month filter
            available_categories: List of available categories for fuzzy matching
            
        Returns:
            str: SQL query string
        """
        query = f"""
            SELECT 
                Category,
                SUM(Amount) as total_amount,
                COUNT(*) as transaction_count
            FROM {self.table_name}
            WHERE 1=1
        """
        
        # Add category filter
        if available_categories:
            category_filter = self.build_category_filter(category, available_categories)
            if category_filter:
                query += f"\n            {category_filter}"
        
        # Add date filter
        if month:
            date_filter = self.build_date_filter(month)
            if date_filter:
                query += f"\n            {date_filter}"
        
        query += "\n            GROUP BY Category"
        
        return query
    
    def build_top_expenses_query(
        self, 
        n: int, 
        category: Optional[str] = None,
        month: Optional[str] = None,
        available_categories: Optional[List[str]] = None
    ) -> str:
        """
        Build SQL query for top N expenses
        
        Args:
            n: Number of top expenses to return
            category: Optional category filter
            month: Optional month filter
            available_categories: List of available categories
            
        Returns:
            str: SQL query string
        """
        query = f"""
            SELECT 
                Notes,
                Amount,
                Date,
                Category,
                ROW_NUMBER() OVER (ORDER BY Amount DESC) as rank
            FROM {self.table_name}
            WHERE 1=1
        """
        
        # Add category filter
        if category and available_categories:
            category_filter = self.build_category_filter(category, available_categories)
            if category_filter:
                query += f"\n            {category_filter}"
        
        # Add date filter
        if month:
            date_filter = self.build_date_filter(month)
            if date_filter:
                query += f"\n            {date_filter}"
        
        query += f"\n            ORDER BY Amount DESC\n            LIMIT {n}"
        
        return query
    
    def build_category_summary_query(
        self, 
        category: str, 
        mode: str = "total",
        month: Optional[str] = None,
        available_categories: Optional[List[str]] = None
    ) -> str:
        """
        Build SQL query for category summary
        
        Args:
            category: Category to summarize
            mode: 'total', 'average', or 'count'
            month: Optional month filter
            available_categories: List of available categories
            
        Returns:
            str: SQL query string
        """
        if mode == "total":
            select_clause = "SUM(Amount) as result_value"
        elif mode == "average":
            select_clause = "AVG(Amount) as result_value"
        elif mode == "count":
            select_clause = "COUNT(*) as result_value"
        else:
            raise ValueError(f"Invalid mode: {mode}")
        
        query = f"""
            SELECT 
                Category,
                {select_clause},
                COUNT(*) as transaction_count
            FROM {self.table_name}
            WHERE 1=1
        """
        
        # Add category filter
        if available_categories:
            category_filter = self.build_category_filter(category, available_categories)
            if category_filter:
                query += f"\n            {category_filter}"
        
        # Add date filter
        if month:
            date_filter = self.build_date_filter(month)
            if date_filter:
                query += f"\n            {date_filter}"
        
        query += "\n            GROUP BY Category"
        
        return query
    
    def build_monthly_expenses_query(
        self, 
        month: str, 
        category: Optional[str] = None,
        available_categories: Optional[List[str]] = None
    ) -> str:
        """
        Build SQL query for listing monthly expenses
        
        Args:
            month: Month to filter by
            category: Optional category filter
            available_categories: List of available categories
            
        Returns:
            str: SQL query string
        """
        query = f"""
            SELECT 
                Date,
                Category,
                Amount,
                Notes
            FROM {self.table_name}
            WHERE 1=1
        """
        
        # Add category filter
        if category and available_categories:
            category_filter = self.build_category_filter(category, available_categories)
            if category_filter:
                query += f"\n            {category_filter}"
        
        # Add date filter
        date_filter = self.build_date_filter(month)
        if date_filter:
            query += f"\n            {date_filter}"
        
        query += "\n            ORDER BY Date DESC, Amount DESC"
        
        return query
    
    def _fuzzy_match_category(self, user_input: str, categories: List[str]) -> Optional[str]:
        """
        Fuzzy match category name
        
        Args:
            user_input: User input category
            categories: Available categories
            
        Returns:
            str: Matched category or None
        """
        if not categories:
            return None
        
        user_input = user_input.lower().strip()
        categories_lower = {c.lower(): c for c in categories}
        
        matches = get_close_matches(user_input, categories_lower.keys(), n=1, cutoff=0.6)
        return categories_lower[matches[0]] if matches else None
    
    def _parse_month_string(self, month_str: str) -> Optional[str]:
        """
        Parse month string to YYYY-MM format
        
        Args:
            month_str: Month string (e.g., '2025-01', 'June 2025')
            
        Returns:
            str: Parsed month in YYYY-MM format or None
        """
        import re
        from datetime import datetime
        
        try:
            # Try ISO format first
            if re.match(r"^\d{4}-\d{2}$", month_str):
                return month_str
            
            # Try MM/YY or MM/YYYY
            if re.match(r"^\d{1,2}/\d{2,4}$", month_str):
                parts = month_str.split("/")
                if len(parts[1]) == 2:
                    dt = datetime.strptime(month_str, "%m/%y")
                else:
                    dt = datetime.strptime(month_str, "%m/%Y")
                return dt.strftime("%Y-%m")
            
            # Try named month formats
            try:
                dt = datetime.strptime(month_str, "%B %Y")  # 'June 2025'
                return dt.strftime("%Y-%m")
            except ValueError:
                dt = datetime.strptime(month_str, "%b %Y")  # 'Jun 2025'
                return dt.strftime("%Y-%m")
                
        except Exception:
            return None 