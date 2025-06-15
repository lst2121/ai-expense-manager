import pandas as pd

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