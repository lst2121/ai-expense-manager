import pandas as pd
import random
from datetime import datetime, timedelta

categories = [
    "Groceries", "Electricity", "Dining Out", "Fuel", "Internet",
    "Clothing", "EMI", "Rent", "Gym", "Subscriptions", "Medical", "Shopping"
]

notes = [
    "Amazon purchase", "Monthly bill", "Weekend dinner", "Petrol pump",
    "Recharge", "Doctor visit", "Netflix", "Zomato", "Flipkart", ""
]

def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    delta = end_date - start_date
    return start_date + timedelta(days=random.randint(0, delta.days))
    
def generate_expense_data(n=50):
    """Generate a DataFrame with random expense data."""
    data = []
    for _ in range(n):
        date = random_date(datetime(2025, 1, 1), datetime(2025, 6, 14))
        category = random.choice(categories)
        amount = round(random.uniform(100, 5000), 2)
        note = random.choice(notes)
        data.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Category": category,
            "Amount": amount,
            "Notes": note
        })
    return pd.DataFrame(data)
df = generate_expense_data(60)
# Save the DataFrame to a CSV file
df.to_csv("data/sample_expenses.csv", index=False)
print("✅ sample_expense.csv generated with", len(df), "rows.")
