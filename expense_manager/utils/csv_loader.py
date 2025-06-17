import pandas as pd
from ..utils.autofill_helpers import autofill_category, infer_category_from_notes

def load_and_prepare_csv(path: str) -> pd.DataFrame:
    """
    Loads a CSV file, converts 'Date' column to datetime, and adds 'Month' column.
    
    Args:
        path (str): Path to the CSV file.
    
    Returns:
        pd.DataFrame: Cleaned and enriched DataFrame.
    """
    try:
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        df['Month'] = df['Date'].dt.strftime('%B')
        return df
    except Exception as e:
        print(f"❌ Error loading or processing CSV: {e}")
        return pd.DataFrame()

def load_expenses_from_csv(file_path: str) -> pd.DataFrame:
    """
    Load expenses from CSV file and infer missing/generic categories.
    """
    df = pd.read_csv(file_path)
    
    # Ensure required columns exist
    required_cols = ['Date', 'Amount', 'Notes']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"CSV missing required column: {col}")
    
    # Add Category column if missing
    if 'Category' not in df.columns:
        df['Category'] = 'Uncategorized'
    
    # Infer categories for missing or generic entries
    mask = (
        df['Category'].isna() | 
        df['Category'].str.strip().str.lower().isin(['miscellaneous', 'other', ''])
    )
    
    df.loc[mask, 'Category'] = df.loc[mask, 'Notes'].apply(infer_category_from_notes)
    
    return df