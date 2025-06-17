import pandas as pd
import sys
import os

# Add project root to path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from tools.compare_category_tool import compare_category_tool


def test_compare_category_tool_basic():
    df = pd.DataFrame({
        "Date": ["2024-04-05", "2024-04-12", "2024-05-01", "2024-06-03", "2024-06-18"],
        "Category": ["Food", "Transport", "Food", "Food", "Transport"],
        "Amount": [200, 150, 180, 160, 300]
    })

    result = compare_category_tool.invoke({
        "df": df,
        "category1": "Food",
        "category2": "Transport",
        "months": None
    })

    assert isinstance(result, dict)
    assert "text" in result and "chart" in result
    assert "Food" in result["text"]
    assert "Transport" in result["text"]
    assert result["chart"] and len(result["chart"]) > 100


def test_compare_category_tool_with_months():
    df = pd.DataFrame({
        "Date": ["2024-04-05", "2024-05-01", "2024-06-03", "2024-06-18"],
        "Category": ["Food", "Food", "Transport", "Food"],
        "Amount": [100, 200, 300, 400]
    })

    result = compare_category_tool.invoke({
        "df": df,
        "category1": "Food",
        "category2": "Transport",
        "months": ["2024-06"]
    })

    assert "2024-06" in result["text"] or "Food" in result["text"]
    assert result["chart"] and len(result["chart"]) > 100


def test_compare_category_tool_invalid_categories():
    df = pd.DataFrame({
        "Date": ["2024-04-01"],
        "Category": ["Entertainment"],
        "Amount": [500]
    })

    result = compare_category_tool.invoke({
        "df": df,
        "category1": "Food",
        "category2": "Travel",
        "months": None
    })

    assert "⚠️" in result["text"]
    assert result["chart"] is None


def test_compare_category_tool_empty_dataframe():
    df = pd.DataFrame(columns=["Date", "Category", "Amount"])

    result = compare_category_tool.invoke({
        "df": df,
        "category1": "Food",
        "category2": "Transport",
        "months": None
    })

    assert "Error" in result["text"] or "⚠️" in result["text"]
    assert result["chart"] is None


def test_compare_category_tool_fuzzy_match():
    df = pd.DataFrame({
        "Date": ["2024-05-01", "2024-05-10"],
        "Category": ["Groceries", "Transportation"],
        "Amount": [250, 320]
    })

    result = compare_category_tool.invoke({
        "df": df,
        "category1": "grocery",
        "category2": "transpo",
        "months": None
    })

    assert "Groceries" in result["text"] or "Transportation" in result["text"]
    assert result["chart"] and len(result["chart"]) > 100


if __name__ == "__main__":
    test_compare_category_tool_basic()
    test_compare_category_tool_with_months()
    test_compare_category_tool_invalid_categories()
    test_compare_category_tool_empty_dataframe()
    test_compare_category_tool_fuzzy_match()

    print("\n✅ All tests passed successfully!")
