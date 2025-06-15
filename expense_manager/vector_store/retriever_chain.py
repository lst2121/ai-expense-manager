# expense_manager/vector_store/retriever_chain.py

from langchain.chains import RetrievalQA
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.vectorstores import VectorStore

def create_retriever_chain(llm: BaseChatModel, retriever: VectorStore) -> RetrievalQA:
    """
    Creates a QA chain using the given retriever and language model.

    Args:
        llm (BaseChatModel): The LLM to answer questions.
        retriever (VectorStore): A vector store retriever.

    Returns:
        RetrievalQA: A retriever-based question answering chain.
    """
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever.as_retriever(),
        return_source_documents=True,
        verbose=True
    )
