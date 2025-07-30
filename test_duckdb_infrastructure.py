#!/usr/bin/env python3
"""
Test script for DuckDB infrastructure
Loads sample data and tests the first tool
"""

import sys
import os
import logging

# Disable LangSmith tracing to prevent shutdown errors
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duckdb_tools.core.duckdb_manager import DuckDBManager
from duckdb_tools.tools.sum_category_expenses_tool import sum_category_expenses_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_infrastructure():
    """Test the DuckDB infrastructure with sample data"""
    
    print("🚀 Testing DuckDB Infrastructure")
    print("=" * 50)
    
    try:
        # Initialize DuckDB manager
        print("📊 Initializing DuckDB manager...")
        db_manager = DuckDBManager("data/expenses.duckdb")
        
        # Load sample CSV
        csv_path = "data/sample_expense.csv"
        if not os.path.exists(csv_path):
            print(f"❌ Sample CSV not found: {csv_path}")
            return False
        
        print(f"📁 Loading CSV: {csv_path}")
        success = db_manager.load_csv_to_table(csv_path, "expenses")
        
        if not success:
            print("❌ Failed to load CSV")
            return False
        
        # Get table info
        print("📋 Getting table information...")
        table_info = db_manager.get_table_info("expenses")
        print(f"   Rows: {table_info['row_count']}")
        print(f"   Categories: {table_info['categories']}")
        print(f"   Date range: {table_info['date_range']}")
        
        # Create views
        print("🔧 Creating database views...")
        db_manager.create_views()
        
        # Test a simple query
        print("🔍 Testing simple query...")
        result = db_manager.execute_query("SELECT SUM(Amount) as total FROM expenses")
        total = result.iloc[0]['total']
        print(f"   Total expenses: ₹{total:.2f}")
        
        # Test the sum category tool
        print("\n🧪 Testing sum_category_expenses_tool...")
        result = sum_category_expenses_tool.invoke({
            "table_name": "expenses",
            "category": "grocery"
        })
        print(f"   Result: {result['text']}")
        
        print("\n✅ Infrastructure test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    success = test_infrastructure()
    sys.exit(0 if success else 1) 