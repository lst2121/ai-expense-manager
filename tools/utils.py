# tools/utils.py

from typing import Optional
from difflib import get_close_matches
import calendar
import re

def fuzzy_match_category(user_input: str, categories: list[str]) -> Optional[str]:
    user_input = user_input.lower().strip()
    categories_lower = {c.lower(): c for c in categories}
    matches = get_close_matches(user_input, categories_lower.keys(), n=1, cutoff=0.6)
    return categories_lower[matches[0]] if matches else None

def parse_month_string(month_str: str) -> Optional[str]:
    month_str = month_str.strip().lower()
    patterns = [
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\-]*(\d{2,4})",
        r"(\d{1,2})[\-/](\d{2,4})"
    ]
    for pat in patterns:
        match = re.match(pat, month_str)
        if match:
            try:
                if pat.startswith("(jan"):
                    month = list(calendar.month_abbr).index(match[1][:3].capitalize())
                    year = int(match[2]) if len(match[2]) == 4 else 2000 + int(match[2])
                else:
                    month = int(match[1])
                    year = int(match[2]) if len(match[2]) == 4 else 2000 + int(match[2])
                return f"{year}-{month:02d}"
            except:
                continue
    return None
