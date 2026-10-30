from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class WebSearchInput(BaseModel):
    query: str = Field(description="Search engine query (e.g. 'current inflation rate in India 2026', 'USD to INR exchange rate today', 'BESCOM electricity bill rates')")
    max_results: Optional[int] = Field(default=3, description="Maximum number of search results to return (default 3)")


@tool("web_search", args_schema=WebSearchInput)
def web_search(query: str, max_results: int = 3) -> str:
    """
    Searches the live web for current economic indicators, inflation statistics,
    currency exchange rates, tax slabs, or merchant/vendor validation.
    Use this whenever internal general ledger data is insufficient or when the user
    asks about macroeconomic conditions, market trends, or external vendors.
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return f"No web search results found for query: '{query}'."

            formatted = []
            for r in results:
                title = r.get("title", "No Title")
                href = r.get("href", "")
                body = r.get("body", "")
                formatted.append(f"Title: {title}\nSource: {href}\nSummary: {body}\n")
            return "\n---\n".join(formatted)
    except Exception as e:
        return f"Web search encountered an error: {str(e)}"

