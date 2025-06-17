# utils/autofill_helpers.py

import pandas as pd
from typing import Optional

def autofill_compare_months_args(arguments: dict) -> dict:
    """
    Auto-fills 'month1' and 'month2' in the arguments dictionary if they are missing.

    It scans the 'Date' column in the provided DataFrame to extract the two most recent months,
    and injects them into the argument dict for compare_months_tool.

    Args:
        arguments (dict): Tool arguments including a 'df' key with a pandas DataFrame.

    Returns:
        dict: Updated arguments with 'month1' and 'month2' added if missing.
    """
    df = arguments.get("df")
    if not isinstance(df, pd.DataFrame) or "Date" not in df.columns:
        return arguments

    if "month1" in arguments and "month2" in arguments:
        return arguments  # Already provided

    recent_months = (
        df["Date"]
        .dropna()
        .dt.to_period("M")
        .drop_duplicates()
        .sort_values(ascending=False)
        .astype(str)
        .tolist()
    )

    if len(recent_months) >= 2:
        arguments.setdefault("month1", recent_months[1])
        arguments.setdefault("month2", recent_months[0])

    return arguments

def infer_category_from_notes(notes: str) -> str:
    """
    Infers the expense category based on keywords in the transaction notes.
    Args:
        notes: Transaction notes or description.
    Returns:
        Inferred category (e.g., 'Shopping', 'Dining', 'Utilities').
    """
    if not notes:
        return "Uncategorized"

    notes_lower = notes.lower()

    # Define keyword-to-category mappings
    category_mappings = {
        "amazon": "Shopping/E-commerce",
        "flipkart": "Shopping/E-commerce",
        "zomato": "Dining",
        "swiggy": "Dining",
        "diesel": "Fuel",
        "petrol": "Fuel",
        "spotify": "Subscriptions",
        "netflix": "Subscriptions",
        "electricity": "Utilities",
        "rent": "Rent",
    }

    for keyword, category in category_mappings.items():
        if keyword in notes_lower:
            return category

    return "Uncategorized"

def autofill_category(notes: str, current_category: Optional[str] = None) -> str:
    """
    Autofills the category based on transaction notes, preserving manual overrides.
    Args:
        notes: Transaction notes or description.
        current_category: Existing category (if any).
    Returns:
        Inferred or existing category.
    """
    if current_category and current_category != "Uncategorized":
        return current_category
    return infer_category_from_notes(notes or "")
