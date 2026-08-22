from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

# --- Document & Processing Schemas ---

class DocumentInfo(BaseModel):
    id: str
    patient_id: str
    filename: str
    file_type: str
    document_type: str
    document_date: Optional[str] = None
    upload_date: str
    page_count: int = 1
    processing_status: str = "processed"
    storage_path: str
    summary: Optional[str] = None

class DocumentListResponse(BaseModel):
    patient_id: str
    documents: List[DocumentInfo]

class DocumentUploadResponse(BaseModel):
    document_id: str
    patient_id: str
    filename: str
    file_type: str
    document_type: str
    document_date: Optional[str] = None
    page_count: int
    chunks_created: int
    observations_extracted: int
    medications_extracted: int
    timeline_event_created: bool
    status: str = "processed"

# --- Structured Data Schemas ---

class MedicalObservationSchema(BaseModel):
    id: Optional[str] = None
    patient_id: str
    document_id: Optional[str] = None
    test_name: str
    value_numeric: Optional[float] = None
    value_text: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: str = "normal"  # normal, high, low, abnormal
    observation_date: Optional[str] = None
    source_page: int = 1

class MedicationSchema(BaseModel):
    id: Optional[str] = None
    patient_id: str
    document_id: Optional[str] = None
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    status: str = "active"  # active, discontinued, unknown
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source_page: int = 1

class TimelineEventSchema(BaseModel):
    id: Optional[str] = None
    patient_id: str
    document_id: Optional[str] = None
    event_date: str
    event_type: str  # blood_test, consultation, prescription, scan, surgery, claim
    title: str
    description: Optional[str] = None

# --- RAG & Chat Schemas ---

class ChatRequest(BaseModel):
    patient_id: str
    question: str
    filter_document_type: Optional[str] = None

class SourceCitation(BaseModel):
    document_id: str
    filename: str
    page: int
    snippet: str

class ChatResponse(BaseModel):
    question: str
    answer: str
    patient_id: str
    sources: List[SourceCitation]

# --- Report AI Summarization & Comparison Schemas ---

class ReportSummarizeResponse(BaseModel):
    document_id: str
    patient_id: str
    filename: str
    document_type: str
    simple_explanation: str
    important_findings: List[str]
    abnormal_values: List[Dict[str, Any]]
    questions_for_doctor: List[str]

class MetricComparisonItem(BaseModel):
    parameter: str
    previous_value: float
    previous_unit: Optional[str]
    previous_date: Optional[str]
    current_value: float
    current_unit: Optional[str]
    current_date: Optional[str]
    change_delta: float
    percentage_change: Optional[float]
    status: str  # increased, decreased, unchanged

class ReportComparisonRequest(BaseModel):
    patient_id: str
    previous_document_id: str
    current_document_id: str

class ReportComparisonResponse(BaseModel):
    patient_id: str
    previous_document_id: str
    current_document_id: str
    metrics: List[MetricComparisonItem]
    ai_explanation: str
    summary_verdict: str

# --- Emergency Snapshot & QR Schemas ---

class CriticalAlert(BaseModel):
    category: str  # allergy, medication_alert, condition
    title: str
    severity: str = "high"
    details: str

class EmergencySnapshotResponse(BaseModel):
    patient_id: str
    full_name: str
    blood_group: Optional[str] = None
    allergies: List[str]
    current_medications: List[str]
    critical_conditions: List[str]
    critical_things_to_know: List[str]
    critical_alerts: List[CriticalAlert]
    emergency_contact: Dict[str, str]

class EmergencyQRRequest(BaseModel):
    patient_id: str

class EmergencyQRResponse(BaseModel):
    patient_id: str
    qr_token: str
    emergency_url: str
    qr_code_base64: str

class EmergencyPublicViewResponse(BaseModel):
    blood_group: Optional[str]
    allergies: List[str]
    critical_conditions: List[str]
    current_medications: List[str]
    critical_alerts: List[str]
    emergency_contact: Dict[str, str]
    disclaimer: str = "EMERGENCY MEDICAL SNAPSHOT - FOR FIRST RESPONDERS ONLY"

# --- Timed Doctor Access & Audit Log Schemas ---

class AccessGrantRequest(BaseModel):
    patient_id: str
    grantee_name: str
    duration_hours: int = 24
    categories: List[str] = Field(default=["all"])

class AccessGrantResponse(BaseModel):
    id: str
    patient_id: str
    grantee_name: str
    access_token: str
    expires_at: str
    scope: Dict[str, Any]
    is_revoked: bool

class AccessLogItem(BaseModel):
    id: str
    patient_id: str
    accessor_name: str
    access_type: str
    resource_accessed: str
    timestamp: str

class AccessLogResponse(BaseModel):
    patient_id: str
    logs: List[AccessLogItem]

# --- Insurance Document Discovery Schemas ---

class RequiredDocStatus(BaseModel):
    document_type: str
    required_name: str
    status: str  # available, missing
    matching_document: Optional[DocumentInfo] = None

class InsuranceClaimCheckRequest(BaseModel):
    patient_id: str
    claim_type: str = "hospitalization"  # hospitalization, surgery, diagnostic, prescription

class InsuranceClaimCheckResponse(BaseModel):
    patient_id: str
    claim_type: str
    readiness_percentage: float
    required_documents: List[RequiredDocStatus]
    missing_document_types: List[str]
    summary_verdict: str
