# Personal Healthcare Medical Vault — AI & Document Intelligence Backend

A standalone, production-oriented **Healthcare Document Intelligence and AI Backend** built with **FastAPI**, **Supabase** (PostgreSQL, `pgvector`, Auth, Storage), **Gemini LLM**, and local **Sentence-Transformers** (`sentence-transformers/all-MiniLM-L6-v2`).

Patients can securely store medical records, extract laboratory observations & medication prescriptions, search records with RAG ("Ask My Medical Records"), compare lab reports deterministically, view a health timeline, manage temporary timed doctor access grants, track privacy audit logs, check insurance claim document readiness, and generate emergency medical snapshots accessible via a secure QR code.

---

## 🏗 System Architecture

```text
                                 MAIN FRONTEND
                                       │
                                       ▼
                                SUPABASE AUTH
                                       │
                                       ▼
                                FASTAPI BACKEND
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
   SUPABASE POSTGRES           DOCUMENT INGESTION              RAG ENGINE
  + STORAGE + PGVECTOR              PIPELINE               (Gemini + MiniLM)
           │                           │                           │
   ┌───────┴───────┐           ┌───────┴───────┐           ┌───────┴───────┐
   │ - Documents   │           │ PDF / Scanned │           │ Patient-Filter│
   │ - Chunks      │           │ Image (OCR)   │           │ Vector Search │
   │ - Labs/Meds   │           │ DOCX / TXT    │           │ Gemini Synth  │
   │ - Timeline    │           └───────┬───────┘           │ Citation Map  │
   │ - Emergency   │                   │                   └───────────────┘
   │ - Access Logs │                   ▼
   └───────────────┘           Normalized Text
                                       │
                               ┌───────┴───────┐
                               ▼               ▼
                        Structured DB      pgvector
                        Labs/Meds/Events    Chunks
```

---

## 🚀 Key Features

1. **Multi-Format Ingestion**:
   - Native PDFs (`pypdf` / `pdfplumber`).
   - Scanned PDFs and Medical Images (`pytesseract` / `PIL` OCR).
   - `.docx` documents (`python-docx`).
   - `.txt` files.
2. **Patient Data Isolation**:
   - Every database query and vector similarity search strictly mandates `patient_id`.
   - Prevents cross-patient data leakage.
3. **Structured Medical Extraction**:
   - Extracts laboratory observations (`test_name`, `value`, `unit`, `reference_range`, `flag`).
   - Extracts prescription medications (`medicine_name`, `dosage`, `frequency`, `status`).
4. **"Ask My Medical Records" (RAG)**:
   - Patient-filtered vector retrieval in `pgvector` (384-dimensional embeddings).
   - Gemini LLM answer generation with strict non-hallucination prompts.
   - Exact source citations (`document_id`, `filename`, `page_number`).
5. **Emergency Health Snapshot & Secure QR**:
   - Pre-computed Emergency Snapshot ("3 Critical Things You Should Know", Blood type, Allergies, Current Meds, Emergency Contacts).
   - Base64 QR code generation (`qrcode`).
   - Public emergency URL token view exposing ONLY minimal emergency data.
6. **Deterministic Lab Report Comparison**:
   - Calculates exact numerical deltas, percentage changes, and status (`increased`, `decreased`, `unchanged`).
   - Generates natural language AI summary.
7. **Timed Doctor/Hospital Access Grants & Audit Logs**:
   - Auto-expiring access tokens with scope restrictions.
   - Privacy audit log recording all access events.
8. **Insurance Claim Document Discovery**:
   - Evaluates patient vault against claim type document requirements and reports claim readiness percentage.

---

## 📁 Repository Structure

```text
rag demo model/
├── api/
│   ├── main.py             # FastAPI app entrypoint, CORS & router registration
│   ├── documents.py        # Upload, list, inspect, and delete documents
│   ├── chat.py             # Patient-filtered RAG chat endpoint
│   ├── reports.py          # AI Report Summarization & Report Comparison
│   ├── timeline.py         # Chronological Health Timeline endpoint
│   ├── medications.py      # Structured Medications endpoint
│   ├── emergency.py        # Emergency Snapshot & Secure QR endpoints
│   ├── access.py           # Doctor Access Grants & Privacy Audit Logs
│   └── insurance.py        # Insurance Document Discovery endpoint
├── ingestion/
│   ├── ingestion_pipeline.py # Format router, normalization, chunking
│   ├── pdf_processor.py      # PDF text & OCR fallback processor
│   ├── image_processor.py    # JPG/PNG medical image OCR processor
│   ├── docx_processor.py     # Word DOCX text & table processor
│   └── txt_processor.py      # Plain TXT processor
├── extraction/
│   ├── medical_extractor.py  # Document classification & date extraction
│   ├── lab_extractor.py      # Lab observations & reference range extraction
│   └── medication_extractor.py # Prescription medication extraction
├── rag/
│   ├── embeddings.py       # Sentence-transformers (all-MiniLM-L6-v2)
│   ├── vectorstore.py      # Supabase pgvector client with hybrid fallback
│   ├── retriever.py        # Patient-isolated document chunk retriever
│   └── generator.py        # Gemini LLM answer generator & citation mapper
├── services/
│   ├── supabase_service.py # PostgreSQL CRUD & Storage management
│   ├── emergency_service.py# Emergency Snapshot compiler & QR builder
│   ├── comparison_service.py# Deterministic report comparison engine
│   ├── access_service.py   # Doctor access grant & audit log service
│   └── insurance_service.py# Insurance claim document readiness checker
├── models/
│   └── schemas.py          # Pydantic data schemas
├── tests/
│   └── test_backend.py     # End-to-end pytest test suite
├── supabase_schema.sql     # Supabase DDL migration script (pgvector, tables, RLS)
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
└── README.md               # Technical documentation
```

---

## 🛠 Database & Supabase DDL Setup

Execute `supabase_schema.sql` in your Supabase SQL Editor:
- Enables `vector` extension.
- Creates `patients`, `documents`, `document_chunks`, `medical_observations`, `medications`, `timeline_events`, `emergency_profiles`, `access_grants`, `access_logs`.
- Creates HNSW vector index on `document_chunks(embedding)`.
- Creates `match_document_chunks` RPC function for patient-isolated vector similarity search.

---

## ⚙️ Environment Configuration

Create a `.env` file from `.env.example`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key
GEMINI_API_KEY=your-google-gemini-api-key
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMERGENCY_BASE_URL=http://localhost:8000
```

---

## 🏃 Running the Backend

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start FastAPI Dev Server
```bash
python -m uvicorn api.main:app --reload --port 8000
```

- Interactive API Docs (Swagger UI): `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 3. Run Automated Test Suite
```bash
python -m pytest tests/ -v
```

---

## 🔌 API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health check |
| `POST` | `/api/documents/upload` | Upload medical document (PDF, JPG/PNG, DOCX, TXT) |
| `GET` | `/api/documents?patient_id=...` | List patient documents |
| `GET` | `/api/documents/{document_id}` | Retrieve document metadata |
| `DELETE` | `/api/documents/{document_id}` | Cascading deletion of document, vectors & metadata |
| `POST` | `/api/chat` | RAG Chat ("Ask My Medical Records") with citations |
| `POST` | `/api/documents/{document_id}/summarize` | AI Medical Report Summarization |
| `POST` | `/api/reports/compare` | Deterministic Report Comparison with AI explanation |
| `GET` | `/api/timeline?patient_id=...` | Chronological Health Timeline |
| `GET` | `/api/medications?patient_id=...` | Structured Medications history |
| `POST` | `/api/emergency-summary` | Generate/Update Emergency Health Snapshot |
| `POST` | `/api/emergency-qr` | Generate Emergency QR Code and Token |
| `GET` | `/api/emergency/{token}` | Public emergency view (Redacted, Minimal data) |
| `POST` | `/api/access-grants` | Create timed Doctor Access Grant |
| `GET` | `/api/access-grants?patient_id=...` | List active Doctor Access Grants |
| `DELETE` | `/api/access-grants/{grant_id}` | Revoke Doctor Access Grant |
| `GET` | `/api/access-logs?patient_id=...` | Privacy Audit Access Logs |
| `POST` | `/api/insurance/claims/check` | Check document readiness for Insurance Claim |
