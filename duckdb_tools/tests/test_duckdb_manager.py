"""
Tests for DuckDB Manager
"""

import unittest
import tempfile
import os
import pandas as pd
from pathlib import Path

# Import the modules to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from duckdb_tools.core.duckdb_manager import DuckDBManager

class TestDuckDBManager(unittest.TestCase):
    """Test cases for DuckDBManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_expenses.duckdb")
        
        # Create sample CSV data
        self.sample_data = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'Amount': [100.0, 200.0, 150.0],
            'Category': ['Grocery', 'Food', 'Grocery'],
            'Notes': ['Milk', 'Lunch', 'Bread']
        })
        
        self.csv_path = os.path.join(self.temp_dir, "sample_expenses.csv")
        self.sample_data.to_csv(self.csv_path, index=False)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test DuckDBManager initialization"""
        db_manager = DuckDBManager(self.db_path)
        self.assertIsNotNone(db_manager.conn)
        self.assertEqual(db_manager.db_path, self.db_path)
        db_manager.close()
    
    def test_load_csv_to_table(self):
        """Test loading CSV to table"""
        db_manager = DuckDBManager(self.db_path)
        
        # Load CSV
        success = db_manager.load_csv_to_table(self.csv_path, "expenses")
        self.assertTrue(success)
        
        # Check if table exists and has data
        result = db_manager.execute_query("SELECT COUNT(*) FROM expenses")
        self.assertEqual(result.iloc[0, 0], 3)
        
        db_manager.close()
    
    def test_execute_query(self):
        """Test executing SQL queries"""
        db_manager = DuckDBManager(self.db_path)
        db_manager.load_csv_to_table(self.csv_path, "expenses")
        
        # Test simple query
        result = db_manager.execute_query("SELECT SUM(Amount) FROM expenses")
        self.assertEqual(result.iloc[0, 0], 450.0)
        
        # Test query with conditions
        result = db_manager.execute_query("SELECT COUNT(*) FROM expenses WHERE Category = 'Grocery'")
        self.assertEqual(result.iloc[0, 0], 2)
        
        db_manager.close()
    
    def test_get_table_info(self):
        """Test getting table information"""
        db_manager = DuckDBManager(self.db_path)
        db_manager.load_csv_to_table(self.csv_path, "expenses")
        
        info = db_manager.get_table_info("expenses")
        
        self.assertEqual(info["row_count"], 3)
        self.assertIn("Grocery", info["categories"])
        self.assertIn("Food", info["categories"])
        self.assertIsNotNone(info["date_range"]["min_date"])
        self.assertIsNotNone(info["date_range"]["max_date"])
        
        db_manager.close()
    
    def test_get_table_schema(self):
        """Test getting table schema"""
        db_manager = DuckDBManager(self.db_path)
        db_manager.load_csv_to_table(self.csv_path, "expenses")
        
        schema = db_manager.get_table_schema("expenses")
        
        self.assertIn("Date", schema["columns"])
        self.assertIn("Amount", schema["columns"])
        self.assertIn("Category", schema["columns"])
        self.assertIn("Notes", schema["columns"])
        self.assertIn("Month", schema["columns"])
        
        db_manager.close()

if __name__ == "__main__":
    unittest.main() 