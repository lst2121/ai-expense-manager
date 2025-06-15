# expense_manager/vector_store/vector_db.py

import os
from langchain_community.vectorstores import FAISS
from expense_manager.vector_store.embedder import Embedder
from expense_manager.vector_store.document_loader import df_to_documents

class VectorDB:
    def __init__(self, persist_path: str = "vector_store/faiss_index"):
        """
        Initializes the vector database using FAISS and HuggingFace embeddings.

        Args:
            persist_path (str): Path to save/load the FAISS index.
        """
        self.persist_path = persist_path
        self.embedder = Embedder().get_model()
        self.vectorstore = None

    def create_from_dataframe(self, df):
        """
        Creates the FAISS vector store from a pandas DataFrame.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        print("🔄 Converting DataFrame to documents...")
        documents = df_to_documents(df)
        print(f"✅ Created {len(documents)} documents.")

        print("📦 Building vector store...")
        self.vectorstore = FAISS.from_documents(documents, self.embedder)

        # Save to disk
        print("💾 Saving vector store to disk...")
        self.vectorstore.save_local(self.persist_path)
        print("✅ Vector store saved at:", self.persist_path)

    def load(self):
        """
        Loads the FAISS vector store from disk.
        """
        if not os.path.exists(self.persist_path):
            raise FileNotFoundError(f"No vector store found at {self.persist_path}")

        print("📂 Loading vector store from disk...")
        self.vectorstore = FAISS.load_local(self.persist_path, self.embedder, allow_dangerous_deserialization=True)
        print("✅ Vector store loaded.")

    def get_vectorstore(self):
        """
        Returns the loaded FAISS vectorstore instance.

        Returns:
            FAISS: The loaded vectorstore.
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not loaded. Call `load()` first.")
        return self.vectorstore
