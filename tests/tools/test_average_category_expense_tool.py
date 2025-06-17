import pandas as pd
import sys
import os

# Add project root to path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from tools.average_category_expense_tool import average_category_expense_tool

def test_average_category_tool_basic():
    df = pd.DataFrame({
        "Date": ["2024-04-01", "2024-04-15", "2024-05-01", "2024-05-20"],
        "Category": ["Food", "Food", "Food", "Food"],
        "Amount": [200, 300, 250, 350]
    })

    result = average_category_expense_tool.invoke({
        "df": df,
        "category": "Food",
        "months": None
    })

    assert isinstance(result, dict)
    assert "text" in result and "chart" in result
    assert "Food" in result["text"]
    assert result["chart"] and len(result["chart"]) > 100

def test_average_category_tool_with_months():
    df = pd.DataFrame({
        "Date": ["2024-04-01", "2024-05-01", "2024-06-01"],
        "Category": ["Transport", "Transport", "Transport"],
        "Amount": [100, 200, 300]
    })

    result = average_category_expense_tool.invoke({
        "df": df,
        "category": "Transport",
        "months": ["2024-06"]
    })

    assert "2024-06" in result["text"] or "Transport" in result["text"]
    assert result["chart"] and len(result["chart"]) > 100

def test_average_category_tool_invalid_category():
    df = pd.DataFrame({
        "Date": ["2024-04-01"],
        "Category": ["Entertainment"],
        "Amount": [500]
    })

    result = average_category_expense_tool.invoke({
        "df": df,
        "category": "NonExistent",
        "months": None
    })

    assert "⚠️" in result["text"]
    assert result["chart"] is None

def test_average_category_tool_empty_dataframe():
    df = pd.DataFrame(columns=["Date", "Category", "Amount"])

    result = average_category_expense_tool.invoke({
        "df": df,
        "category": "Food",
        "months": None
    })

    assert "Error" in result["text"] or "⚠️" in result["text"]
    assert result["chart"] is None

def test_average_category_tool_fuzzy_match():
    df = pd.DataFrame({
        "Date": ["2024-05-01", "2024-05-10"],
        "Category": ["Groceries", "Groceries"],
        "Amount": [250, 320]
    })

    result = average_category_expense_tool.invoke({
        "df": df,
        "category": "grocery",
        "months": None
    })

    assert "Groceries" in result["text"]
    assert result["chart"] and len(result["chart"]) > 100


if __name__ == "__main__":
    test_average_category_tool_basic()
    test_average_category_tool_with_months()
    test_average_category_tool_invalid_category()
    test_average_category_tool_empty_dataframe()
    test_average_category_tool_fuzzy_match()

    print("\n✅ All average category expense tool tests passed!")
