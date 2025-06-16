from langgraph_app.graph import expense_analysis_app
import pandas as pd

# Sample test data
data = {
    "Date": [
        "2025-06-20", "2025-06-15", "2025-06-10", "2025-06-04",
        "2025-05-22", "2025-05-10"
    ],
    "Category": [
        "Rent", "Groceries", "Shopping", "Subscriptions",
        "Shopping", "Groceries"
    ],
    "Amount": [2300, 750.25, 1450, 485.52, 1200, 670],
    "Notes": [
        "Monthly Rent", "Big Bazaar", "Flipkart", "Netflix",
        "Amazon", "Local Store"
    ]
}

sample_df = pd.DataFrame(data)

# Test prompts
queries = [
    "What are my top 2 expenses?",
    "Show expenses for June 2025",
    "Top 1 grocery expense",
    "What did I spend the most on?",
    "Show me rent expenses in June 2025",
    "Breakdown of shopping expenses in May 2025",
    "How much did I spend on healthcare?",  # Fallback case
    "Did I spend on food last month?"       # Another fallback
]

print("\n🔎 Running LangGraph Tests:\n")

for query in queries:
    print(f"\n🟡 Query: {query}")

    inputs = {
        "query": query,
        "df": sample_df
    }

    output = expense_analysis_app.invoke(inputs)

    print("\n✅ Final Output:")
    print(output.get("result", "❌ No result returned"))

    print("\n" + "=" * 60)
    print(f"🔧 Tool Used: {output.get('invoked_tool', '❌ Not recorded')}")
