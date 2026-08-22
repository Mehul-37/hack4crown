from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from rag.retriever import retriever
from rag.generator import generator
from services.supabase_service import supabase_service
from services.access_service import access_service

router = APIRouter(prefix="/api/chat", tags=["Ask My Medical Records RAG"])

@router.post("", response_model=ChatResponse)
def ask_medical_records(request: ChatRequest):
    """
    Core RAG Chat Endpoint ("Ask My Medical Records").
    Retrieves patient-filtered vector chunks from pgvector, synthesizes response via Gemini LLM,
    and returns exact source citations (document ID, filename, page number).
    """
    if not request.patient_id or not request.question:
        raise HTTPException(status_code=400, detail="patient_id and question are required")

    # 1. Patient-isolated retrieval
    retrieved_chunks = retriever.retrieve(
        question=request.question,
        patient_id=request.patient_id
    )

    # 2. Get document metadata map for accurate citations
    patient_docs = supabase_service.list_documents(request.patient_id)
    doc_map = {d["id"]: d for d in patient_docs}

    # 3. Gemini answer generation
    response = generator.generate_answer(
        question=request.question,
        patient_id=request.patient_id,
        retrieved_chunks=retrieved_chunks,
        doc_metadata_map=doc_map
    )

    # Log action
    access_service.log_access(
        patient_id=request.patient_id,
        accessor_name="Patient",
        access_type="rag_chat",
        resource_accessed=f"Queried RAG: '{request.question[:40]}...'"
    )

    return response
