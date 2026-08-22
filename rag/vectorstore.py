import os
import math
import uuid
from typing import List, Dict, Any, Optional

class VectorStore:
    """
    Manages vector embeddings and chunk storage in Supabase pgvector.
    Provides local in-memory fallback for testing when Supabase credentials are missing.
    Strictly enforces patient_id filtering for patient isolation.
    """
    def __init__(self):
        self.supabase_client = None
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key and "example.supabase.co" not in supabase_url:
            try:
                from supabase import create_client
                self.supabase_client = create_client(supabase_url, supabase_key)
            except Exception:
                self.supabase_client = None

        # In-memory vector store fallback
        self._local_chunks: List[Dict[str, Any]] = []

    def store_chunks(self, patient_id: str, document_id: str, chunks_data: List[Dict[str, Any]]) -> int:
        """
        Stores chunks with embeddings.
        chunks_data: [{"content": "...", "page_number": 1, "embedding": [...], "metadata": {...}}]
        """
        stored_count = 0
        records = []
        for item in chunks_data:
            chunk_id = str(uuid.uuid4())
            record = {
                "id": chunk_id,
                "document_id": document_id,
                "patient_id": patient_id,
                "content": item["content"],
                "page_number": item.get("page_number", 1),
                "embedding": item["embedding"],
                "metadata": item.get("metadata", {})
            }
            records.append(record)

        if self.supabase_client:
            try:
                res = self.supabase_client.table("document_chunks").insert(records).execute()
                stored_count = len(res.data) if res.data else len(records)
                return stored_count
            except Exception as e:
                # Fallback to local store on error
                pass

        # Fallback store
        self._local_chunks.extend(records)
        return len(records)

    def similarity_search(self, query_embedding: List[float], patient_id: str, top_k: int = 5, match_threshold: float = 0.15) -> List[Dict[str, Any]]:
        """
        Patient-isolated vector similarity search using cosine distance.
        """
        if self.supabase_client:
            try:
                rpc_res = self.supabase_client.rpc("match_document_chunks", {
                    "query_embedding": query_embedding,
                    "match_threshold": match_threshold,
                    "match_count": top_k,
                    "filter_patient_id": patient_id
                }).execute()

                if rpc_res.data:
                    return rpc_res.data
            except Exception:
                pass

        # Fallback local cosine similarity search
        results = []
        patient_chunks = [c for c in self._local_chunks if c["patient_id"] == patient_id]

        for chunk in patient_chunks:
            emb = chunk["embedding"]
            sim = self._cosine_similarity(query_embedding, emb)
            if sim >= match_threshold:
                results.append({
                    "id": chunk["id"],
                    "document_id": chunk["document_id"],
                    "patient_id": chunk["patient_id"],
                    "content": chunk["content"],
                    "page_number": chunk["page_number"],
                    "metadata": chunk.get("metadata", {}),
                    "similarity": sim
                })

        # Sort descending by similarity score
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def delete_document_chunks(self, document_id: str, patient_id: str):
        """Removes all vector chunks for a deleted document."""
        if self.supabase_client:
            try:
                self.supabase_client.table("document_chunks").delete().eq("document_id", document_id).eq("patient_id", patient_id).execute()
            except Exception:
                pass

        self._local_chunks = [c for c in self._local_chunks if not (c["document_id"] == document_id and c["patient_id"] == patient_id)]

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

vector_store = VectorStore()
