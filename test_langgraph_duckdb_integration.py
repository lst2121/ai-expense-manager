#!/usr/bin/env python3
"""
Test LangGraph integration with DuckDB tools
"""

import sys
import os
import logging

# Disable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_app.graph import expense_analysis_app
from duckdb_tools.core.duckdb_manager import DuckDBManager
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_langgraph_duckdb_integration():
    """Test LangGraph with DuckDB tools"""
    
    print("🚀 Testing LangGraph + DuckDB Integration")
    print("=" * 60)
    
    try:
        # Initialize DuckDB
        print("📊 Initializing DuckDB...")
        db_manager = DuckDBManager("data/expenses.duckdb")
        
        # Load sample data
        csv_path = "data/sample_expense.csv"
        if not os.path.exists(csv_path):
            print(f"❌ Sample CSV not found: {csv_path}")
            return False
        
        print(f"📁 Loading CSV: {csv_path}")
        success = db_manager.load_csv_to_table(csv_path, "expenses")
        
        if not success:
            print("❌ Failed to load CSV")
            return False
        
        # Create views
        db_manager.create_views()
        
        # Test queries
        test_queries = [
            "What are my top 5 expenses?",
            "How much did I spend on groceries?",
            "Show me the total for transportation category",
            "What's the average expense in entertainment category?"
        ]
        
        print("\n" + "="*60)
        print("🧪 Testing LangGraph Queries")
        print("="*60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}️⃣ Testing: {query}")
            print("-" * 40)
            
            try:
                # Invoke LangGraph
                result = expense_analysis_app.invoke({
                    "query": query,
                    "df": pd.DataFrame(),  # Empty for DuckDB tools
                    "memory": []
                })
                
                # Display results
                print(f"✅ Result: {result.get('result', 'No result')[:100]}...")
                print(f"🛠️ Tool: {result.get('invoked_tool', 'Unknown')}")
                
                # Check for chart
                if result.get('chart'):
                    print("📊 Chart: Generated ✅")
                else:
                    print("📊 Chart: None")
                
                # Check memory
                memory = result.get('memory', [])
                print(f"🧠 Memory entries: {len(memory)}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n✅ LangGraph + DuckDB integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    success = test_langgraph_duckdb_integration()
    sys.exit(0 if success else 1) 