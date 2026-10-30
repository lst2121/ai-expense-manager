#!/usr/bin/env python3
"""
Comprehensive test script for DuckDB tools
Tests all three tools with sample data
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
from duckdb_tools.tools.top_expenses_tool import top_expenses_tool
from duckdb_tools.tools.category_summary_tool import category_summary_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_tools():
    """Test all three DuckDB tools"""
    
    print("🚀 Testing All DuckDB Tools")
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
        table_info = db_manager.get_table_info("expenses")
        print(f"📋 Loaded {table_info['row_count']} rows")
        print(f"📋 Categories: {table_info['categories'][:5]}...")  # Show first 5
        
        # Create views
        db_manager.create_views()
        
        print("\n" + "="*50)
        print("🧪 Testing Tools")
        print("="*50)
        
        # Test 1: Sum Category Expenses Tool
        print("\n1️⃣ Testing sum_category_expenses_tool...")
        result = sum_category_expenses_tool.invoke({
            "category": "grocery",
            "month": "2025-01"
        })
        print(f"   Result: {result['text']}")
        
        # Test 2: Top Expenses Tool
        print("\n2️⃣ Testing top_expenses_tool...")
        result = top_expenses_tool.invoke({
            "n": 5,
            "category": "food"
        })
        print(f"   Result: {result['text'][:100]}...")  # Show first 100 chars
        print(f"   Chart generated: {'Yes' if result['chart'] else 'No'}")
        
        # Test 3: Category Summary Tool (Total mode)
        print("\n3️⃣ Testing category_summary_tool (total mode)...")
        result = category_summary_tool.invoke({
            "category": "transport",
            "mode": "total"
        })
        print(f"   Result: {result['text']}")
        print(f"   Chart generated: {'Yes' if result['chart'] else 'No'}")
        
        # Test 4: Category Summary Tool (Average mode)
        print("\n4️⃣ Testing category_summary_tool (average mode)...")
        result = category_summary_tool.invoke({
            "category": "entertainment",
            "mode": "average"
        })
        print(f"   Result: {result['text']}")
        print(f"   Chart generated: {'Yes' if result['chart'] else 'No'}")
        
        # Test 5: Category Summary Tool (Count mode)
        print("\n5️⃣ Testing category_summary_tool (count mode)...")
        result = category_summary_tool.invoke({
            "category": "shopping",
            "mode": "count"
        })
        print(f"   Result: {result['text']}")
        print(f"   Chart generated: {'Yes' if result['chart'] else 'No'}")
        
        print("\n✅ All tools tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    success = test_all_tools()
    sys.exit(0 if success else 1) 