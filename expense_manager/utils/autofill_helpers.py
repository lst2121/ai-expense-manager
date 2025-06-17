# utils/autofill_helpers.py

import pandas as pd
from typing import Optional
from fuzzywuzzy import fuzz

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

# Mapping of keywords to categories (expand as needed)
CATEGORY_KEYWORDS = {
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
    "grocery": "Groceries",
    "groceries": "Groceries",
    "food": "Dining",
    "dining": "Dining",
    "restaurant": "Dining",
    "cafe": "Dining",
}

def infer_category_from_notes(notes, threshold=80):
    """
    Infer the category from transaction notes using keyword and fuzzy matching.
    Args:
        notes (str): Transaction notes/description.
        threshold (int): Minimum fuzzy match score (0-100).
    Returns:
        str: Inferred category or "Uncategorized".
    """
    if not notes:
        return "Uncategorized"
    
    notes_lower = notes.lower()
    
    # Exact keyword match
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in notes_lower:
            return category
    
    # Fuzzy match if no exact match found
    for keyword, category in CATEGORY_KEYWORDS.items():
        if fuzz.partial_ratio(keyword, notes_lower) >= threshold:
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
