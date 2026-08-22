import os
from typing import List
from sentence_transformers import SentenceTransformer

# Load free/local sentence-transformer model for 384-dimensional embeddings
MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

class EmbeddingEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            cls._instance.model = SentenceTransformer(MODEL_NAME)
        return cls._instance

    def embed_text(self, text: str) -> List[float]:
        """Generate a 384-dimensional vector embedding for a single text string."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

# Singleton helper instance
embedding_engine = EmbeddingEngine()
