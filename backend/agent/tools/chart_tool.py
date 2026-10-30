import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class ChartSpecInput(BaseModel):
    chart_type: str = Field(
        description="Type of chart to render: 'bar', 'area', 'pie', or 'line'"
    )
    title: str = Field(
        description="Clean, executive chart title (e.g., 'Monthly Spending Trends (2025)')"
    )
    x_key: str = Field(
        description="The object property key for the horizontal axis or pie slice label (e.g., 'category', 'period', 'vendor')"
    )
    y_keys: List[str] = Field(
        description="The object property keys for the vertical metric values (e.g., ['total_spend'])"
    )
    data: List[Dict[str, Any]] = Field(
        description="Array of data records containing the keys specified in x_key and y_keys"
    )
    description: Optional[str] = Field(
        default="",
        description="Brief financial takeaway or commentary explaining the visual"
    )


@tool("generate_chart_spec", args_schema=ChartSpecInput)
def generate_chart_spec(
    chart_type: str,
    title: str,
    x_key: str,
    y_keys: List[str],
    data: List[Dict[str, Any]],
    description: Optional[str] = ""
) -> str:
    """
    Generates a structured JSON chart specification formatted specifically for Recharts frontend rendering.
    Call this tool whenever the user asks for a chart, graph, visualization, or breakdown.
    Supported chart types: 'bar', 'area', 'pie', 'line'.
    """
    normalized_type = chart_type.lower()
    if normalized_type not in ["bar", "area", "pie", "line"]:
        normalized_type = "bar"

    spec = {
        "__chart__": True,
        "chart_type": normalized_type,
        "title": title,
        "description": description or "",
        "x_key": x_key,
        "y_keys": y_keys,
        "data": data,
    }

    return json.dumps(spec)

