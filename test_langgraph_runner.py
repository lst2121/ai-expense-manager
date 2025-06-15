# test_langgraph_runner.py

from langgraph_app.graph import expense_analysis_app
import pandas as pd

# Sample dataframe
sample_data = {
    "Date": ["2025-06-04", "2025-06-10", "2025-06-15", "2025-05-22", "2025-06-20"],
    "Category": ["Subscriptions", "Shopping", "Groceries", "Shopping", "Rent"],
    "Amount": [485.52, 1450.00, 750.25, 1200.00, 2300.00],
    "Notes": ["Netflix", "Flipkart", "Big Bazaar", "Amazon", "Monthly Rent"]
}
df = pd.DataFrame(sample_data)

# Queries to test
queries = [
    "What are my top 2 expenses?",
    "Show expenses for June 2025",
    "Top 1 grocery expense",
    "What did I spend the most on?",
    "Show me rent expenses in June 2025",
    "Breakdown of shopping expenses in May 2025"
]

print("\n\U0001F50E Running LangGraph Tests:\n")

for query in queries:
    print("\U0001F7E1 Query:", query)
    
    # Initialize a fresh runner each time to avoid state carryover
    app = expense_analysis_app
    result = app.invoke({"query": query, "df": df})
    
    print("\n\u2705 Final Output:")
    print(result.get("result", "❌ No result key in output."))
    print("\n" + "=" * 60 + "\n")
