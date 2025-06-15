# test_tool_runner.py

import pandas as pd
from tools.query_dataframe_tool import query_tool

# Sample dataframe similar to your CSV
data = {
    "Date": ["2025-06-04", "2025-06-10", "2025-06-15", "2025-05-22", "2025-06-20"],
    "Category": ["Subscriptions", "Shopping", "Groceries", "Shopping", "Rent"],
    "Amount": [485.52, 1450.00, 750.25, 1200.00, 2300.00],
    "Notes": ["Netflix", "Flipkart", "Big Bazaar", "Amazon", "Monthly Rent"]
}
df = pd.DataFrame(data)

print("\n🧪 Test 1: Top 2 expenses overall")
result = query_tool.invoke({
    "df": df,
    "operation": "top_n_expenses",
    "n": 2
})
print(result)

print("\n🧪 Test 2: Top 2 groceries expenses in June 2025")
result = query_tool.invoke({
    "df": df,
    "operation": "top_n_expenses",
    "category": "Groceries",
    "month": "2025-06",
    "n": 2
})
print(result)

print("\n🧪 Test 3: All expenses in June 2025")
result = query_tool.invoke({
    "df": df,
    "operation": "list_month_expenses",
    "month": "2025-06"
})
print(result)

print("\n🧪 Test 4: All expenses in May 2025")
result = query_tool.invoke({
    "df": df,
    "operation": "list_month_expenses",
    "month": "2025-05"
})
print(result)

print("\n🧪 Test 5: Unknown operation")
result = query_tool.invoke({
    "df": df,
    "operation": "unknown_operation"
})
print(result)

print("\n🧪 Test 6: Invalid month format")
result = query_tool.invoke({
    "df": df,
    "operation": "list_month_expenses",
    "month": "June-2025"
})
print(result)
