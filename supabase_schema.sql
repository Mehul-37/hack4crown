-- Healthcare Medical Vault Supabase DDL Schema
-- Includes PostgreSQL tables, pgvector support, indexes, match RPC function, and RLS policies

-- 1. Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID, -- Link to supabase auth.users if available
    full_name TEXT NOT NULL,
    date_of_birth DATE,
    gender TEXT,
    blood_group TEXT,
    allergies TEXT[] DEFAULT '{}',
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL, -- pdf, jpg, png, docx, txt
    document_type TEXT DEFAULT 'unknown', -- blood_report, prescription, mri_report, etc.
    document_date DATE,
    upload_date TIMESTAMPTZ DEFAULT NOW(),
    page_count INT DEFAULT 1,
    processing_status TEXT DEFAULT 'processed', -- pending, processing, processed, failed
    storage_path TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Document Chunks Table with pgvector
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    page_number INT DEFAULT 1,
    embedding vector(384), -- Dimension 384 for sentence-transformers/all-MiniLM-L6-v2
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast vector similarity search filtered by patient_id
CREATE INDEX IF NOT EXISTS idx_document_chunks_patient_id ON document_chunks(patient_id);

-- 5. Medical Observations (Labs / Diagnostic Results)
CREATE TABLE IF NOT EXISTS medical_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    test_name TEXT NOT NULL,
    value_numeric NUMERIC,
    value_text TEXT NOT NULL,
    unit TEXT,
    reference_range TEXT,
    flag TEXT DEFAULT 'normal', -- normal, high, low, abnormal
    observation_date DATE,
    source_page INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Medications Table
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    medicine_name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    status TEXT DEFAULT 'active', -- active, discontinued, unknown
    start_date DATE,
    end_date DATE,
    source_page INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Timeline Events
CREATE TABLE IF NOT EXISTS timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_type TEXT NOT NULL, -- blood_test, consultation, prescription, scan, surgery, claim
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Emergency Profiles (Pre-computed Health Snapshot)
CREATE TABLE IF NOT EXISTS emergency_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL UNIQUE REFERENCES patients(id) ON DELETE CASCADE,
    blood_group TEXT,
    allergies JSONB DEFAULT '[]'::jsonb,
    current_medications JSONB DEFAULT '[]'::jsonb,
    critical_conditions JSONB DEFAULT '[]'::jsonb,
    critical_alerts JSONB DEFAULT '[]'::jsonb,
    emergency_contacts JSONB DEFAULT '[]'::jsonb,
    qr_token TEXT UNIQUE,
    token_created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Doctor/Hospital Access Grants
CREATE TABLE IF NOT EXISTS access_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    grantee_name TEXT NOT NULL, -- Doctor or Hospital Name
    access_token TEXT UNIQUE NOT NULL,
    scope JSONB DEFAULT '{"categories": ["all"]}'::jsonb, -- e.g. ["blood_report", "prescription"]
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE
);

-- 10. Audit Access Logs
CREATE TABLE IF NOT EXISTS access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    accessor_name TEXT NOT NULL,
    access_type TEXT NOT NULL, -- emergency_qr, doctor_grant, patient_login
    resource_accessed TEXT NOT NULL,
    ip_address TEXT,
    accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Stored Procedure for Patient-Isolated Vector Similarity Search
CREATE OR REPLACE FUNCTION match_document_chunks (
    query_embedding vector(384),
    match_threshold float DEFAULT 0.2,
    match_count int DEFAULT 5,
    filter_patient_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    patient_id uuid,
    content text,
    page_number int,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.patient_id,
        dc.content,
        dc.page_number,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE (filter_patient_id IS NULL OR dc.patient_id = filter_patient_id)
      AND 1 - (dc.embedding <=> query_embedding) >= match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
