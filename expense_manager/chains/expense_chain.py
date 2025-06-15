# expense_manager/chains/expense_chain.py

from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import pandas as pd
from expense_manager import config
from pydantic import SecretStr

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
