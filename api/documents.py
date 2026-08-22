import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from datetime import datetime

from ingestion.ingestion_pipeline import IngestionPipeline
from extraction.medical_extractor import MedicalExtractor
from extraction.lab_extractor import extract_lab_observations
from extraction.medication_extractor import extract_medications
from rag.embeddings import embedding_engine
from rag.vectorstore import vector_store
from services.supabase_service import supabase_service
from services.access_service import access_service
from models.schemas import DocumentUploadResponse, DocumentInfo, DocumentListResponse

router = APIRouter(prefix="/api/documents", tags=["Documents"])
pipeline = IngestionPipeline()
extractor = MedicalExtractor()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    patient_id: str = Form(...)
):
    """
    Multi-format document upload pipeline (PDF, JPG/PNG, DOCX, TXT).
    Saves file to Supabase Storage, runs OCR/extraction, chunking, embedding generation,
    pgvector indexing, and structured database extraction (labs, medications, timeline events).
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    doc_id = str(uuid.uuid4())
    filename = file.filename

    # Ensure patient exists
    supabase_service.get_or_create_patient(patient_id)

    # 1. Ingestion (format detection, OCR, text extraction, page-aware chunking)
    try:
        processed = pipeline.process_file(file_bytes, filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

    full_text = processed["full_text"]
    file_type = processed["file_type"]
    page_count = processed["page_count"]
    raw_chunks = processed["chunks"]

    # 2. Extract metadata & structured medical data
    doc_type = extractor.classify_document(full_text, filename)
    doc_date = extractor.extract_document_date(full_text)
    
    # Extract lab observations & medications
    obs_list = extract_lab_observations(full_text)
    med_list = extract_medications(full_text)

    # 3. Store original file in Supabase Storage
    storage_path = supabase_service.save_document_file(patient_id, doc_id, filename, file_bytes)

    # 4. Save document record in PostgreSQL
    doc_record = {
        "id": doc_id,
        "patient_id": patient_id,
        "filename": filename,
        "file_type": file_type,
        "document_type": doc_type,
        "document_date": doc_date,
        "upload_date": datetime.now().isoformat(),
        "page_count": page_count,
        "processing_status": "processed",
        "storage_path": storage_path,
        "summary": full_text[:500]
    }
    supabase_service.insert_document(doc_record)

    # 5. Generate local sentence-transformer embeddings and store in pgvector
    chunk_records = []
    chunk_texts = [c["content"] for c in raw_chunks]
    embeddings = embedding_engine.embed_batch(chunk_texts)

    for idx, c in enumerate(raw_chunks):
        chunk_records.append({
            "content": c["content"],
            "page_number": c["page_number"],
            "embedding": embeddings[idx],
            "metadata": {
                "document_id": doc_id,
                "patient_id": patient_id,
                "filename": filename,
                "document_type": doc_type,
                "document_date": doc_date
            }
        })
    
    chunks_created = vector_store.store_chunks(patient_id, doc_id, chunk_records)

    # 6. Save structured observations to DB
    db_obs = []
    for o in obs_list:
        db_obs.append({
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "document_id": doc_id,
            "test_name": o["test_name"],
            "value_numeric": o["value_numeric"],
            "value_text": o["value_text"],
            "unit": o["unit"],
            "reference_range": o["reference_range"],
            "flag": o["flag"],
            "observation_date": doc_date,
            "source_page": o["source_page"]
        })
    supabase_service.insert_observations(db_obs)

    # 7. Save structured medications to DB
    db_meds = []
    for m in med_list:
        db_meds.append({
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "document_id": doc_id,
            "medicine_name": m["medicine_name"],
            "dosage": m["dosage"],
            "frequency": m["frequency"],
            "status": m["status"],
            "source_page": m["source_page"]
        })
    supabase_service.insert_medications(db_meds)

    # 8. Create timeline event
    timeline_event = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "document_id": doc_id,
        "event_date": doc_date or datetime.now().strftime("%Y-%m-%d"),
        "event_type": doc_type,
        "title": f"Uploaded {doc_type.replace('_', ' ').title()}: {filename}",
        "description": f"Extracted {len(obs_list)} lab parameters and {len(med_list)} prescribed medications."
    }
    supabase_service.insert_timeline_event(timeline_event)

    # Log action
    access_service.log_access(
        patient_id=patient_id,
        accessor_name="Patient",
        access_type="patient_upload",
        resource_accessed=f"Uploaded document '{filename}' ({doc_id})"
    )

    return DocumentUploadResponse(
        document_id=doc_id,
        patient_id=patient_id,
        filename=filename,
        file_type=file_type,
        document_type=doc_type,
        document_date=doc_date,
        page_count=page_count,
        chunks_created=chunks_created,
        observations_extracted=len(obs_list),
        medications_extracted=len(med_list),
        timeline_event_created=True,
        status="processed"
    )

@router.get("", response_model=DocumentListResponse)
def list_patient_documents(patient_id: str):
    """List all medical documents belonging to the authenticated patient."""
    docs = supabase_service.list_documents(patient_id)
    doc_infos = [DocumentInfo(**d) for d in docs]
    return DocumentListResponse(patient_id=patient_id, documents=doc_infos)

@router.get("/{document_id}", response_model=DocumentInfo)
def get_document(document_id: str, patient_id: str):
    """Retrieve document metadata by document ID."""
    doc = supabase_service.get_document(document_id, patient_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentInfo(**doc)

@router.delete("/{document_id}")
def delete_document(document_id: str, patient_id: str):
    """
    Cascading document deletion: removes storage file, PostgreSQL metadata,
    document chunks, pgvector embeddings, observations, and derived timeline events.
    """
    doc = supabase_service.get_document(document_id, patient_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    vector_store.delete_document_chunks(document_id, patient_id)
    supabase_service.delete_document(document_id, patient_id)

    access_service.log_access(
        patient_id=patient_id,
        accessor_name="Patient",
        access_type="patient_delete",
        resource_accessed=f"Deleted document '{doc['filename']}' ({document_id})"
    )

    return {"message": f"Document {document_id} and all associated vector embeddings successfully deleted."}
