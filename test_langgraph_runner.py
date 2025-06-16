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
    "Compare May and June spending",
    "Compare shopping between May and June",
    "How much did I spend on groceries in May?",
    "How much did I spend in June?",
    "Summarize my past spending"
]

print("\n🔎 LangGraph Expense Analysis – Test Suite\n")

# ✅ Initialize memory once
memory = []

for query in queries:
    print(f"\n🟡 User Query: {query}")

    # ✅ Use current memory and sample data
    inputs = {
        "query": query,
        "df": sample_df,
        "memory": memory
    }

    try:
        output = expense_analysis_app.invoke(inputs)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        continue

    # ✅ Update memory for next query
    memory = output.get("memory", memory)

    result = output.get("result", "❌ No result returned")
    tool_used = output.get("invoked_tool", "❌ Tool not identified")
    tool_input = output.get("tool_input", {})

    print("\n✅ Result:")
    print(result)

    print("\n🔧 Tool Used:", tool_used)
    print("🧾 Tool Input:", tool_input)

    print("\n" + "-" * 60)

# ✅ Show final memory summary at the end
print("\n🧠 Final Memory State:")
for i, entry in enumerate(memory):
    print(f"{i+1}. {entry['query']} → {entry['result']}")
