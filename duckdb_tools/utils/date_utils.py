"""
Date utility functions for DuckDB tools
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Union, List, Optional

logger = logging.getLogger(__name__)

class DateUtils:
    """
    Utility functions for date operations in SQL queries
    """
    
    @staticmethod
    def resolve_time_period(value: str) -> Union[str, List[str], None]:
        """
        Resolve time period strings to SQL-compatible date ranges
        
        Args:
            value: Time period string (e.g., 'this month', 'last 3 months')
            
        Returns:
            Union[str, List[str], None]: Resolved date(s) or None
        """
        today = datetime.today()
        value = value.lower().strip()
        
        # Helper to format month
        def ym(dt):
            return dt.strftime("%Y-%m")
        
        # Case 1: "this month"
        if value == "this month":
            return ym(today)
        
        # Case 2: "last month"
        if value == "last month":
            last_month = (today.replace(day=1) - timedelta(days=1))
            return ym(last_month)
        
        # Case 3: "last N months"
        match = re.match(r"last (\d+) months", value)
        if match:
            n = int(match.group(1))
            months = []
            current = today.replace(day=1)
            for _ in range(n):
                current -= timedelta(days=1)
                months.append(ym(current))
                current = current.replace(day=1)
            return months[::-1]
        
        # Case 4: "last quarter" = last 3 full months
        if value == "last quarter":
            months = []
            current = today.replace(day=1)
            for _ in range(3):
                current -= timedelta(days=1)
                months.append(ym(current))
                current = current.replace(day=1)
            return months[::-1]
        
        # Case 5: "this year"
        if value == "this year":
            return [f"{today.year}-{str(m).zfill(2)}" for m in range(1, today.month + 1)]
        
        # Case 6: valid absolute YYYY-MM
        if re.match(r"\d{4}-\d{2}", value):
            return value
        
        return None  # Unknown format
    
    @staticmethod
    def build_date_range_filter(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        month: Optional[str] = None
    ) -> str:
        """
        Build SQL date filter clause
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            month: Month in YYYY-MM format
            
        Returns:
            str: SQL WHERE clause for date filtering
        """
        conditions = []
        
        if month:
            conditions.append(f"Month = '{month}'")
        
        if start_date:
            conditions.append(f"Date >= '{start_date}'")
        
        if end_date:
            conditions.append(f"Date <= '{end_date}'")
        
        if conditions:
            return " AND ".join(conditions)
        
        return ""
    
    @staticmethod
    def parse_month_string(month_str: str) -> Optional[str]:
        """
        Parse month string to YYYY-MM format
        
        Args:
            month_str: Month string (e.g., '2025-01', 'June 2025')
            
        Returns:
            str: Parsed month in YYYY-MM format or None
        """
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
    
    @staticmethod
    def get_current_month() -> str:
        """
        Get current month in YYYY-MM format
        
        Returns:
            str: Current month
        """
        return datetime.today().strftime("%Y-%m")
    
    @staticmethod
    def get_last_n_months(n: int) -> List[str]:
        """
        Get last N months in YYYY-MM format
        
        Args:
            n: Number of months to get
            
        Returns:
            List[str]: List of months
        """
        months = []
        current = datetime.today().replace(day=1)
        
        for _ in range(n):
            current -= timedelta(days=1)
            months.append(current.strftime("%Y-%m"))
            current = current.replace(day=1)
        
        return months[::-1] 