# main.py

from expense_manager.utils.csv_loader import load_and_prepare_csv
from expense_manager.vector_store.vector_db import VectorDB
from expense_manager.vector_store.retriever_chain import create_retriever_chain
from langchain_deepseek import ChatDeepSeek
from expense_manager import config
from pydantic import SecretStr


def main():
    # Step 1: Load and prepare the CSV
    csv_path = "data/sample_expense.csv"
    df = load_and_prepare_csv(csv_path)
    print("✅ Data loaded and prepared.")

    # Step 2: Setup vector DB
    persist_path = "vector_store/faiss_index"
    vdb = VectorDB(persist_path=persist_path)
    vdb.create_from_dataframe(df)
    vdb.load()
    print("✅ Vector store created and loaded.")

    # Step 3: Load LLM (DeepSeek)
    llm = ChatDeepSeek(
        temperature=config.TEMPERATURE,
        model=config.DEEPSEEK_MODEL_NAME,
        api_key=SecretStr(config.DEEPSEEK_API_KEY),
        base_url=config.BASE_URL
    )

    # Step 4: Create QA chain
    qa_chain = create_retriever_chain(llm=llm, retriever=vdb.get_vectorstore())

    # Step 5: Run test query
    query = "What were my total expenses in February?"
    result = qa_chain.invoke(query)

    # Step 6: Show results
    print("\n💬 Question:", query)
    print("🧠 Answer:", result['result'])

    print("\n📄 Source Documents:")
    for i, doc in enumerate(result["source_documents"], 1):
        print(f"\n--- Source {i} ---")
        print(doc.page_content)

if __name__ == "__main__":
    main()
