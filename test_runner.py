from langgraph_app.graph import expense_analysis_app
import pandas as pd

# Sample dataframe
data = {
    "Date": [
        "2025-06-01", "2025-06-05", "2025-06-12",
        "2025-05-02", "2025-05-15", "2025-04-10",
        "2025-05-20", "2025-06-18"
    ],
    "Category": [
        "Groceries", "Transportation", "Groceries",
        "Transportation", "Groceries", "Entertainment",
        "Rent", "Rent"
    ],
    "Amount": [400, 250, 300, 180, 220, 500, 1000, 1200],
    "Notes": [
        "Big Bazaar", "Bus fare", "Online order",
        "Train", "Local store", "Movie night",
        "May rent", "June rent"
    ]
}
df = pd.DataFrame(data)

# Queries covering all tools from OPERATION_TO_TOOL

queries = [
    # 1. top_n_expenses
    "What were my top 3 expenses in June?",

    # 2. list_month_expenses
    "Show all my expenses for May 2025.",

    # 3. sum_category_expenses
    "How much did I spend on groceries?",

    # 4. date_range_expense
    "How much did I spend on entertainment between 2025-04-01 and 2025-04-30?",

    # 5. summarize_memory
    "Summarize my past spending.",

    # 6. compare_months
    "Compare my spending in May 2025 and June 2025.",

    # 7. compare_category
    "Compare groceries and transportation expenses for May and June.",

    # 8. average_category_expense
    "What’s my average rent payment in May and June?",

    # 9. category_summary
    "Give me a summary of groceries for May and June.",

    # Additional queries to cover variations
    "Show expenses for last month.",
    "Top 2 expenses in transportation.",
    "What did I spend most on?",
    "How much did I spend on rent last month?",
]

# Run test queries
for query in queries:
    print(f"\n🔍 Query: {query}")
    result = expense_analysis_app.invoke({
        "query": query,
        "df": df,
        "memory": []
    })
    print(f"🧾 Result: {result.get('result', result)}")
    if "chart" in result:
        print(f"📊 Chart Length: {len(result['chart']) if result['chart'] else 'No Chart'}")
