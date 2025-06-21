import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, path: str = "vector_db", collection_name: str = "documents"):
        """
        Initializes the VectorStore client.
        For local development, this will create a persistent database in the specified path.
        """
        db_path = Path(path)
        db_path.mkdir(exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(db_path))
        
        # Using a pre-built sentence-transformer model for embedding.
        # This simplifies the process as ChromaDB handles the embedding generation.
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.sentence_transformer_ef
        )
        logger.info(f"Vector store initialized. Collection '{collection_name}' is ready.")

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """
        Adds documents and their metadata to the collection.
        ChromaDB will automatically convert documents to embeddings.
        """
        if not documents:
            return
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )