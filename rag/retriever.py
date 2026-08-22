from typing import List, Dict, Any
from rag.embeddings import embedding_engine
from rag.vectorstore import vector_store

class Retriever:
    """
    Patient-isolated document chunk retriever.
    Converts question to query embedding and retrieves patient's relevant document chunks.
    """
    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def retrieve(self, question: str, patient_id: str) -> List[Dict[str, Any]]:
        query_embedding = embedding_engine.embed_text(question)
        chunks = vector_store.similarity_search(
            query_embedding=query_embedding,
            patient_id=patient_id,
            top_k=self.top_k
        )
        return chunks

retriever = Retriever()
