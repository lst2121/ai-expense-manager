# test_runner.py

from langgraph_app.graph import expense_analysis_app
import pandas as pd

# Sample dataframe
data = {
    "Date": [
        "2025-06-01", "2025-06-05", "2025-06-12",
        "2025-05-02", "2025-05-15", "2025-04-10"
    ],
    "Category": [
        "Groceries", "Transportation", "Groceries",
        "Transportation", "Groceries", "Entertainment"
    ],
    "Amount": [400, 250, 300, 180, 220, 500],
    "Notes": [
        "Big Bazaar", "Bus fare", "Online order",
        "Train", "Local store", "Movie night"
    ]
}
df = pd.DataFrame(data)

# ✅ Queries to test
queries = [
    "Compare grocery and transport expenses",
    "What's my average spending on groceries?",
    "Show average spending by category",
    "How much did I spend on entertainment in April?",
    "Compare my spending in May and June",
    "What were my top 3 expenses in June?",
    "Summarize my spending in the last 3 months",
    "Summarize my past spending.",
    "Give me a summary of groceries in May and June",
    "Show detailed summary for transport category",
    "Summarize spending on groceries",

]

# Run test queries
for query in queries:
    print(f"\n🔍 Query: {query}")
    result = expense_analysis_app.invoke({
        "query": query,
        "df": df,
        "memory": []
    })
    print(f"🧾 Result: {result['result']}")
    if "chart" in result:
        print(f"📊 Chart Length: {len(result['chart']) if result['chart'] else 'No Chart'}")
        
