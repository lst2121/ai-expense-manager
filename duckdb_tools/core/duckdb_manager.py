# type: ignore
"""
DuckDB Manager for expense data operations
Handles CSV loading, SQL queries, and database management
"""

import os
import logging
from typing import Dict, List, Optional, Union
import pandas as pd
import duckdb
from pathlib import Path

logger = logging.getLogger(__name__)

class DuckDBManager:
    """
    Manages DuckDB database operations for expense data
    """
    
    def __init__(self, db_path: str = "data/expenses.duckdb"):
        """
        Initialize DuckDB manager
        
        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self._ensure_data_directory()
        self._connect()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _connect(self):
        """Establish connection to DuckDB"""
        try:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to DuckDB: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise
    
    @property
    def connection(self):
        """Get database connection, ensuring it exists"""
        assert self.conn is not None, "Database connection not established"
        return self.conn
    
    def load_csv_to_table(self, csv_path: str, table_name: str = "expenses") -> bool:
        """
        Load CSV file into DuckDB table
        
        Args:
            csv_path: Path to CSV file
            table_name: Name of the table to create/overwrite
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(csv_path):
                logger.error(f"CSV file not found: {csv_path}")
                return False
            
            if self.conn is None:
                logger.error("Database connection not established")
                return False
            
            # Drop existing table if it exists
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Create table from CSV
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
            
            # Add Month column for easier querying
            self.conn.execute(f"""
                ALTER TABLE {table_name} 
                ADD COLUMN Month VARCHAR;
            """)
            
            # Update Month column with formatted date
            self.conn.execute(f"""
                UPDATE {table_name} 
                SET Month = strftime('%Y-%m', Date)
                WHERE Date IS NOT NULL;
            """)
            
            # Get row count
            result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            row_count = result[0] if result else 0
            
            logger.info(f"Loaded {row_count} rows into table '{table_name}' from {csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load CSV to table: {e}")
            return False
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame
        
        Args:
            query: SQL query string
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            if self.conn is None:
                raise RuntimeError("Database connection not established")
            
            result = self.conn.execute(query)
            df = result.fetchdf()
            logger.debug(f"Query executed successfully, returned {len(df)} rows")
            return df
            
        except duckdb.Error as e:
            logger.error(f"DuckDB SQL error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise
    
    def get_table_schema(self, table_name: str = "expenses") -> Dict:
        """
        Get table schema information
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dict: Schema information
        """
        try:
            result = self.conn.execute(f"DESCRIBE {table_name}").fetchdf()
            schema = {
                "columns": result["column_name"].tolist(),
                "types": result["column_type"].tolist(),
                "nulls": result["null"].tolist(),
                "defaults": result["default"].tolist()
            }
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return {}
    
    def get_table_info(self, table_name: str = "expenses") -> Dict:
        """
        Get basic table information
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dict: Table information
        """
        try:
            # Get row count
            count_result = self.conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()
            row_count = count_result[0] if count_result else 0
            
            # Get unique categories
            categories_result = self.conn.execute(f"SELECT DISTINCT Category FROM {table_name}").fetchdf()
            categories = categories_result["Category"].tolist() if not categories_result.empty else []
            
            # Get date range
            date_result = self.conn.execute(f"""
                SELECT MIN(Date) as min_date, MAX(Date) as max_date 
                FROM {table_name} 
                WHERE Date IS NOT NULL
            """).fetchone()
            
            date_range = {
                "min_date": date_result[0] if date_result and date_result[0] else None,
                "max_date": date_result[1] if date_result and date_result[1] else None
            }
            
            return {
                "row_count": row_count,
                "categories": categories,
                "date_range": date_range,
                "table_name": table_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}
    
    def create_views(self):
        """Create useful views for common queries"""
        try:
            # Monthly summary view
            self.conn.execute("""
                CREATE OR REPLACE VIEW monthly_summary AS
                SELECT 
                    Month,
                    COUNT(*) as transaction_count,
                    SUM(Amount) as total_amount,
                    AVG(Amount) as avg_amount
                FROM expenses
                GROUP BY Month
                ORDER BY Month
            """)
            
            # Category summary view
            self.conn.execute("""
                CREATE OR REPLACE VIEW category_summary AS
                SELECT 
                    Category,
                    COUNT(*) as transaction_count,
                    SUM(Amount) as total_amount,
                    AVG(Amount) as avg_amount
                FROM expenses
                GROUP BY Category
                ORDER BY total_amount DESC
            """)
            
            logger.info("Created database views for common queries")
            
        except Exception as e:
            logger.error(f"Failed to create views: {e}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 