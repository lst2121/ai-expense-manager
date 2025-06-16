# tools/utils.py

from typing import Optional
from difflib import get_close_matches
import calendar
import re
from datetime import datetime, timedelta

def fuzzy_match_category(user_input: str, categories: list[str]) -> Optional[str]:
    user_input = user_input.lower().strip()
    categories_lower = {c.lower(): c for c in categories}
    matches = get_close_matches(user_input, categories_lower.keys(), n=1, cutoff=0.6)
    return categories_lower[matches[0]] if matches else None

def parse_month_string(month_str: str) -> str:
    """
    Parses a string like 'June 2025', '06/25', '2025-06' into '2025-06' format.

    Returns:
    - 'YYYY-MM' as string, or None if unrecognized
    """
    try:
        # Try ISO format first
        if re.match(r"^\d{4}-\d{2}$", month_str):
            return month_str

        # Try MM/YY or MM/YYYY
        if re.match(r"^\d{1,2}/\d{2,4}$", month_str):
            dt = datetime.strptime(month_str, "%m/%y") if len(month_str.split("/")[1]) == 2 else datetime.strptime(month_str, "%m/%Y")
            return dt.strftime("%Y-%m")

        # Try named month formats like 'June 2025'
        try:
            dt = datetime.strptime(month_str, "%B %Y")  # 'June 2025'
            return dt.strftime("%Y-%m")
        except ValueError:
            dt = datetime.strptime(month_str, "%b %Y")  # 'Jun 2025'
            return dt.strftime("%Y-%m")

    except Exception:
        return None

def resolve_time_period(value: str):
    today = datetime.today()
    value = value.lower().strip()

    # Helper to format month
    def ym(dt):
        return dt.strftime("%Y-%m")

    # Case 1: "this month"
    if value == "this month":
        return ym(today)

    # Case 2: "last month"
    if value == "last month":
        last_month = (today.replace(day=1) - timedelta(days=1))
        return ym(last_month)

    # Case 3: "last N months"
    match = re.match(r"last (\d+) months", value)
    if match:
        n = int(match.group(1))
        months = []
        current = today.replace(day=1)
        for _ in range(n):
            current -= timedelta(days=1)
            months.append(ym(current))
            current = current.replace(day=1)
        return months[::-1]

    # Case 4: "last quarter" = last 3 full months
    if value == "last quarter":
        months = []
        current = today.replace(day=1)
        for _ in range(3):
            current -= timedelta(days=1)
            months.append(ym(current))
            current = current.replace(day=1)
        return months[::-1]

    # Case 5: "this year"
    if value == "this year":
        return [f"{today.year}-{str(m).zfill(2)}" for m in range(1, today.month + 1)]

    # Case 6: valid absolute YYYY-MM
    if re.match(r"\d{4}-\d{2}", value):
        return value

    return value  # Unknown format → fallback