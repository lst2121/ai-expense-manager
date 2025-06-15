"""
Vector store embedder module using HuggingFace sentence-transformers.
This class wraps LangChain's HuggingFaceEmbeddings interface.
"""

from langchain_huggingface import HuggingFaceEmbeddings


class Embedder:
    """
    Wrapper class for HuggingFaceEmbeddings using sentence-transformers.
    
    Args:
        model_name (str): Name of the sentence-transformers model to use.
                          Default is "all-MiniLM-L6-v2", a fast and efficient model.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes the HuggingFace embedding model.
        """
        self.model = HuggingFaceEmbeddings(model_name=model_name)

    def get_model(self):
        """
        Returns the embedding model instance for use with vector stores.

        Returns:
            HuggingFaceEmbeddings: The loaded embedding model.
        """
        return self.model
