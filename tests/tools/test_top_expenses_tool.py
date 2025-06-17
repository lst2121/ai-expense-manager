import pandas as pd
import sys
import os

# Add project root to path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from tools.top_expenses_tool import top_expenses_tool


def test_top_expenses_tool_basic():
    df = pd.DataFrame({
        "Date": ["2024-06-01", "2024-06-02", "2024-06-03"],
        "Category": ["Food", "Transport", "Food"],
        "Amount": [100, 200, 150],
        "Notes": ["Pizza", "Uber", "Groceries"]
    })

    result = top_expenses_tool.invoke({
        "df": df,
        "n": 2,
        "category": None,
        "month": None
    })

    assert isinstance(result, dict)
    assert "text" in result and "chart" in result
    assert "Top 2 expenses" in result["text"]
    assert result["chart"] is not None and len(result["chart"]) > 100


def test_top_expenses_tool_with_category_and_month():
    df = pd.DataFrame({
        "Date": ["2024-06-01", "2024-06-05", "2024-05-10"],
        "Category": ["Food", "Food", "Food"],
        "Amount": [300, 100, 500],
        "Notes": ["Dinner", "Snacks", "Old Food"]
    })

    result = top_expenses_tool.invoke({
        "df": df,
        "n": 1,
        "category": "food",
        "month": "2024-06"
    })

    assert "Top 1 expenses" in result["text"]
    assert "2024-06" in result["text"]
    assert result["chart"] is not None


def test_top_expenses_tool_fuzzy_category():
    df = pd.DataFrame({
        "Date": ["2024-05-01"],
        "Category": ["Groceries"],
        "Amount": [400],
        "Notes": ["Monthly groceries"]
    })

    result = top_expenses_tool.invoke({
        "df": df,
        "n": 1,
        "category": "grocery",
        "month": "2024-05"
    })

    assert "Groceries" in result["text"]
    assert result["chart"] is not None


def test_top_expenses_tool_invalid_category():
    df = pd.DataFrame({
        "Date": ["2024-06-01"],
        "Category": ["Food"],
        "Amount": [250],
        "Notes": ["Breakfast"]
    })

    result = top_expenses_tool.invoke({
        "df": df,
        "n": 1,
        "category": "invalidcat",
        "month": None
    })

    assert "⚠️ No matching category" in result["text"]
    assert result["chart"] is None


def test_top_expenses_tool_empty_dataframe():
    df = pd.DataFrame(columns=["Date", "Category", "Amount", "Notes"])

    result = top_expenses_tool.invoke({
        "df": df,
        "n": 3,
        "category": None,
        "month": None
    })

    assert "⚠️" in result["text"]
    assert result["chart"] is None


if __name__ == "__main__":
    test_top_expenses_tool_basic()
    test_top_expenses_tool_with_category_and_month()
    test_top_expenses_tool_fuzzy_category()
    test_top_expenses_tool_invalid_category()
    test_top_expenses_tool_empty_dataframe()
    print("\n✅ All top_expenses_tool tests passed!")
