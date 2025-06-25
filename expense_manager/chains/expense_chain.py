# expense_manager/chains/expense_chain.py

from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import pandas as pd
from expense_manager import config
from pydantic import SecretStr
from ..utils.csv_loader import load_expenses_from_csv
from typing import Optional

def create_expense_chain():
    llm = ChatDeepSeek(
        temperature=config.TEMPERATURE,
        model=config.DEEPSEEK_MODEL_NAME,
        api_key=SecretStr(config.DEEPSEEK_API_KEY),
        base_url=config.BASE_URL
    )

    template = """
    You are a financial assistant. Given the following expense data:

    {df_str}

    Answer the user's question: "{question}"

    Be concise and accurate. Return only the answer.
    """

    prompt = PromptTemplate.from_template(template)

    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=config.DEBUG_MODE
    )

    return chain

def run_expense_chain(chain, df: pd.DataFrame, query: str):
    df_str = df.to_string(index=False)
    response = chain.run({
        "df_str": df_str,
        "question": query
    })
    return response

class ExpenseChain:
    def __init__(self, secret_value: str = ""):
        """
        Initialize ExpenseChain with optional secret value.
        Args:
            secret_value: Secret string for authentication (defaults to empty string).
        """
        self.df = pd.DataFrame()
        self.secret_value = SecretStr(secret_value)

    def load_data(self, file_path: str) -> None:
        """
        Load expense data from CSV file with automatic category inference.
        Args:
            file_path: Path to CSV file.
        """
        try:
            self.df = load_expenses_from_csv(file_path)
            print(f"✅ Successfully loaded {len(self.df)} expenses with inferred categories")
        except Exception as e:
            print(f"❌ Error loading expenses: {e}")
            self.df = pd.DataFrame()

    # ... rest of the class methods remain unchanged ...
