#!/usr/bin/env python3

"""
🧪 Multi-Step Planning Test Suite

Tests the new multi-step planning and execution system.
"""

from langgraph_app.graph import expense_analysis_app
import pandas as pd

# Enhanced sample data for better testing
data = {
    "Date": [
        "2025-05-01", "2025-05-15", "2025-05-20", "2025-05-25",
        "2025-06-01", "2025-06-10", "2025-06-15", "2025-06-20", 
        "2025-07-01", "2025-07-05", "2025-07-10", "2025-07-15"
    ],
    "Category": [
        "Groceries", "Transportation", "Rent", "Groceries",
        "Groceries", "Transportation", "Rent", "Groceries",
        "Groceries", "Transportation", "Dining", "Entertainment"
    ],
    "Amount": [
        400, 150, 1200, 250,
        450, 200, 1200, 300,
        500, 180, 350, 400
    ],
    "Notes": [
        "Walmart May", "Bus fare", "May rent", "Local store",
        "Costco June", "Uber rides", "June rent", "Groceries June",
        "Whole Foods", "Gas", "Restaurant", "Movies"
    ]
}

df = pd.DataFrame(data)

def test_query(query_desc: str, query: str):
    """Test a single query and display results."""
    print(f"\n" + "="*80)
    print(f"🧪 TEST: {query_desc}")
    print(f"📝 Query: {query}")
    print("="*80)
    
    try:
        result = expense_analysis_app.invoke({
            "query": query,
            "df": df,
            "memory": []
        })
        
        print(f"\n✅ RESULT:")
        print(result.get("result", "No result"))
        
        # Show multi-step info if available
        if result.get("is_multi_step"):
            print(f"\n🔄 Multi-step execution detected!")
            step_results = result.get("step_results", [])
            print(f"📊 Executed {len(step_results)} steps")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def main():
    print("🚀 Multi-Step Planning Test Suite")
    print(f"📊 Test Dataset: {len(df)} expense records")
    print(f"📅 Date Range: {df['Date'].min()} to {df['Date'].max()}")
    
    # Test cases: Simple to Complex
    test_cases = [
        ("Simple Category Query", "How much did I spend on groceries?"),
        ("Simple Monthly Query", "Show my expenses for June 2025"),
        ("Multi-Step Trend Analysis", "Show grocery trends over the last 3 months"),
        ("Complex Comparison", "Compare grocery vs transportation spending patterns across May, June, and July"),
        ("Multi-Category Analysis", "Find my top 3 expenses, then compare the categories involved"),
        ("Trend + Insight", "Show spending trends by month, then identify which category increased the most"),
        ("Complex Time Analysis", "Compare May groceries to June transportation, then show if July dining exceeded either")
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for desc, query in test_cases:
        if test_query(desc, query):
            successful_tests += 1
    
    print(f"\n" + "="*80)
    print(f"🎯 TEST SUMMARY")
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Multi-step planning is working perfectly!")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print("="*80)

if __name__ == "__main__":
    main() 