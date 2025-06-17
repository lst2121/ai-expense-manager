# utils/autofill_helpers.py

import pandas as pd

def autofill_compare_months_args(arguments: dict) -> dict:
    """
    Auto-fills 'month1' and 'month2' in the arguments dictionary if they are missing.

    It scans the 'Date' column in the provided DataFrame to extract the two most recent months,
    and injects them into the argument dict for compare_months_tool.

    Args:
        arguments (dict): Tool arguments including a 'df' key with a pandas DataFrame.

    Returns:
        dict: Updated arguments with 'month1' and 'month2' added if missing.
    """
    df = arguments.get("df")
    if not isinstance(df, pd.DataFrame) or "Date" not in df.columns:
        return arguments

    if "month1" in arguments and "month2" in arguments:
        return arguments  # Already provided

    recent_months = (
        df["Date"]
        .dropna()
        .dt.to_period("M")
        .drop_duplicates()
        .sort_values(ascending=False)
        .astype(str)
        .tolist()
    )

    if len(recent_months) >= 2:
        arguments.setdefault("month1", recent_months[1])
        arguments.setdefault("month2", recent_months[0])

    return arguments
