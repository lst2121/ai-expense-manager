from langchain_core.documents import Document
import pandas as pd

def df_to_documents(df: pd.DataFrame) -> list[Document]:
    """
    Converts a DataFrame to a list of LangChain Document objects.
    
    Args:
        df (pd.DataFrame): The DataFrame to convert.
        
    Returns:
        list[Document]: List of Document objects containing DataFrame data.
    """
    documents = []
    for _, row in df.iterrows():
        content = (
            f"Date: {row['Date']}\n"
            f"Month: {row.get('Month', '')}\n"  # 👈 Added for better month-based QA
            f"Category: {row['Category']}\n"
            f"Amount: {row['Amount']}\n"
            f"Notes: {row['Notes']}"
        )
        
        metadata = {
            "date": str(row["Date"]),
            "category": row["Category"],
            "month": row.get("Month", ""),
            "notes": row["Notes"]
        }
        documents.append(Document(page_content=content, metadata=metadata))
    return documents
