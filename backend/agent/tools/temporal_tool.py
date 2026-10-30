import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import tool


@tool("get_current_datetime")
def get_current_datetime(timezone_str: str = "Asia/Kolkata") -> str:
    """
    Returns the current real-world date, time, day of the week, fiscal quarter, and year.
    Call this tool whenever the user refers to relative time concepts such as
    'today', 'yesterday', 'this week', 'last month', 'this year', or 'current quarter'
    so that you know the exact current temporal anchor before querying financial data.
    """
    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = datetime.timezone.utc

    now = datetime.datetime.now(tz)
    quarter = (now.month - 1) // 3 + 1

    return (
        f"Current Date: {now.strftime('%Y-%m-%d')}\n"
        f"Current Time: {now.strftime('%H:%M:%S')}\n"
        f"Day of Week: {now.strftime('%A')}\n"
        f"Current Month: {now.strftime('%B (%m)')}\n"
        f"Current Quarter: Q{quarter}\n"
        f"Current Year: {now.year}\n"
        f"Timezone: {timezone_str}\n"
        f"ISO 8601: {now.isoformat()}"
    )

