from tools.date_range_expense_tool import date_range_expense_tool
import pandas as pd

df = pd.read_csv("data/sample_expense.csv")

print("Available categories:", df["Category"].unique().tolist())

result = date_range_expense_tool.invoke({
    "df": df,
    "start_date": "2025-05-01",
    "end_date": "2025-06-10",
    "category": "subscription"  # or try exact match if needed
})

print("\nTool Output:\n", result)
