import pandas as pd
import sys
import os
import pytest
from pydantic import ValidationError

# Add project root to path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from tools.category_summary_tool import category_summary_tool


def test_category_summary_tool_total():
    df = pd.DataFrame({
        "Date": ["2025-06-01", "2025-06-15", "2025-05-10", "2025-04-10"],
        "Category": ["Grocery", "Grocery", "Grocery", "Grocery"],
        "Amount": [1200, 800, 950, 1100]
    })

    result = category_summary_tool.invoke({
        "df": df,
        "category": "grocery",
        "mode": "total"
    })

    assert isinstance(result, dict)
    assert "text" in result
    assert "₹" in result["text"]
    assert "Total" in result["text"]


def test_category_summary_tool_average():
    df = pd.DataFrame({
        "Date": ["2025-04-01", "2025-05-01", "2025-06-01"],
        "Category": ["Utilities", "Utilities", "Utilities"],
        "Amount": [300, 400, 500]
    })

    result = category_summary_tool.invoke({
        "df": df,
        "category": "utilities",
        "mode": "average"
    })

    assert "Average per month" in result["text"]
    assert "Utilities" in result["text"]


def test_category_summary_tool_count():
    df = pd.DataFrame({
        "Date": ["2025-06-01", "2025-06-10", "2025-06-20"],
        "Category": ["Health", "Health", "Health"],
        "Amount": [300, 200, 100]
    })

    result = category_summary_tool.invoke({
        "df": df,
        "category": "health",
        "mode": "count"
    })

    assert "Transactions" in result["text"]
    assert "3" in result["text"]


def test_category_summary_tool_fuzzy_match():
    df = pd.DataFrame({
        "Date": ["2025-05-01", "2025-05-10"],
        "Category": ["Groceries", "Groceries"],
        "Amount": [250, 320]
    })

    result = category_summary_tool.invoke({
        "df": df,
        "category": "grocery",  # fuzzy match test
        "mode": "total"
    })

    assert "Groceries" in result["text"]
    assert "₹" in result["text"]


def test_category_summary_tool_invalid_mode():
    df = pd.DataFrame({
        "Date": ["2025-05-01"],
        "Category": ["Travel"],
        "Amount": [500]
    })

    result = category_summary_tool.invoke({
        "df": df,
        "category": "Travel",
        "mode": "something"
    })

    assert "Invalid mode" in result["text"]


def test_category_summary_tool_missing_category():
    df = pd.DataFrame({
        "Date": ["2025-05-01"],
        "Category": ["Food"],
        "Amount": [100]
    })

    # 'category' is a required argument; invoking without should raise a ValidationError
    with pytest.raises(ValidationError):
        category_summary_tool.invoke({
            "df": df,
            "mode": "total"
        })


def test_category_summary_tool_no_data_found():
    df = pd.DataFrame({
        "Date": ["2025-05-01"],
        "Category": ["Entertainment"],
        "Amount": [500]
    })

    result = category_summary_tool.invoke({
        "df": df,
        "category": "Grocery",
        "mode": "total"
    })

    assert "Could not match category" in result["text"] or "No records found" in result["text"]


if __name__ == "__main__":
    test_category_summary_tool_total()
    test_category_summary_tool_average()
    test_category_summary_tool_count()
    test_category_summary_tool_fuzzy_match()
    test_category_summary_tool_invalid_mode()
    test_category_summary_tool_missing_category()
    test_category_summary_tool_no_data_found()

    print("\n✅ All category summary tool tests passed!")
