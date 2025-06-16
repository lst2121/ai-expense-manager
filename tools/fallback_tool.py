# tools/fallback_tool.py

from typing_extensions import TypedDict
import pandas as pd
from langchain_core.tools import tool


class FallbackQueryInput(TypedDict):
    """
    Input schema for the fallback tool.

    Attributes:
        query (str): The user's original query.
        df (pd.DataFrame): Optional expense dataframe, in case future fallback logic needs it.
    """
    query: str
    df: pd.DataFrame


@tool
def fallback_tool(data: FallbackQueryInput) -> str:
    """
    Handles vague or unrecognized user queries gracefully.

    This tool is called when other tools cannot handle the query. It generates
    a helpful fallback message to guide the user.

    Parameters:
        data (FallbackQueryInput): A dict containing the original query and optionally the expense dataframe.

    Returns:
        str: A friendly fallback message.
    """
    query = data["query"]

    # Very basic fallback logic
    return (
        f"🤖 Sorry, I couldn't understand your request: '{query}'.\n\n"
        "You can ask me things like:\n"
        "- 'What are my top 3 expenses?'\n"
        "- 'Show shopping expenses in June 2025'\n"
        "- 'List all rent payments'\n\n"
        "Try rephrasing your query to include a category, month, or amount."
    )
