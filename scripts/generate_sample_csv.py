import pandas as pd
import random
from datetime import datetime, timedelta

# Categories and associated notes
categories = {
    "groceries": ["Walmart", "Trader Joe’s", "Costco", "Local Market"],
    "rent": ["Monthly rent", "Partial rent", "Advance rent"],
    "utilities": ["Electricity bill", "Water bill", "Internet", "Gas bill"],
    "dining": ["Coffee", "Lunch out", "Pizza", "Fast food", "Dinner with friends"],
    "entertainment": ["Netflix", "Movie night", "Concert", "Board game", "Arcade"],
    "transportation": ["Uber", "Metro pass", "Fuel", "Bus pass"],
    "subscriptions": ["Spotify", "YouTube", "Adobe", "VPN", "Medium"],
    "healthcare": ["Pharmacy", "Dental checkup", "Eye test", "Blood test"]
}

def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    delta = end_date - start_date
    return start_date + timedelta(days=random.randint(0, delta.days))

def generate_expense_data(n=200):
    """Generate a DataFrame with structured random expense data."""
    data = []
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 6, 30)

    for _ in range(n):
        date = random_date(start_date, end_date)
        category = random.choice(list(categories.keys()))
        note = random.choice(categories[category])
        amount = round(random.uniform(5, 1200), 2)

        data.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Category": category,
            "Amount": amount,
            "Notes": note
        })

    return pd.DataFrame(data)

# Generate and save
df = generate_expense_data(200)
df.to_csv("data/sample_expense.csv", index=False)
print("✅ sample_expense.csv generated with", len(df), "rows.")
