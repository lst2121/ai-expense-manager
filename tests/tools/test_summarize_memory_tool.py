import pandas as pd
import sys
import os

# Add project root to path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from tools.summarize_memory_tool import summarize_memory_tool


def test_summarize_memory_with_df():
    df = pd.DataFrame({
        "Date": ["2024-05-01", "2024-05-15", "2024-06-01"],
        "Category": ["Food", "Transport", "Health"],
        "Amount": [250, 150, 300]
    })

    result = summarize_memory_tool.invoke({
        "df": df
    })

    assert isinstance(result, str)
    assert "Summary of" in result
    assert "Total Recorded Spending" in result
    assert "Food" in result or "Transport" in result or "Health" in result


def test_summarize_memory_empty_df():
    df = pd.DataFrame(columns=["Date", "Category", "Amount"])

    result = summarize_memory_tool.invoke({
        "df": df
    })

    assert "invalid" in result.lower() or "empty" in result.lower()


def test_summarize_memory_with_mocked_memory():
    memory = [
        {
            "tool_name": "query_tool",
            "tool_args": {"month": "2024-05", "category": "Groceries"},
            "result": "2024-05-01 | Groceries | ₹120.00\n2024-05-10 | Groceries | ₹180.00",
            "query": "How much was spent on groceries in May?"
        },
        {
            "tool_name": "query_tool",
            "tool_args": {"month": "2024-06", "category": "Transport"},
            "result": "2024-06-05 | Transport | ₹300.00",
            "query": "What was the transport cost in June?"
        }
    ]

    result = summarize_memory_tool.invoke({
        "memory": memory
    })

    assert isinstance(result, str)
    assert "Summary" in result
    assert "Groceries" in result
    assert "Transport" in result
    assert "₹600.00" in result or "₹" in result


def test_summarize_memory_empty_memory():
    result = summarize_memory_tool.invoke({
        "memory": []
    })

    assert "🧠" in result or "empty" in result.lower()


if __name__ == "__main__":
    test_summarize_memory_with_df()
    test_summarize_memory_empty_df()
    test_summarize_memory_with_mocked_memory()
    test_summarize_memory_empty_memory()

    print("\n✅ All summarize_memory_tool tests passed successfully!")
