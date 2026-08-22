from fastapi import APIRouter, HTTPException
from models.schemas import (
    ReportSummarizeResponse,
    ReportComparisonRequest,
    ReportComparisonResponse
)
from services.supabase_service import supabase_service
from services.comparison_service import comparison_service
from extraction.lab_extractor import extract_lab_observations

router = APIRouter(tags=["Report AI Features"])

@router.post("/api/documents/{document_id}/summarize", response_model=ReportSummarizeResponse)
def summarize_report(document_id: str, patient_id: str):
    """
    AI Medical Report Summarizer.
    Generates educational summary: simple explanation, key findings, flagged abnormal lab values, and suggested questions for doctor.
    """
    doc = supabase_service.get_document(document_id, patient_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    obs = supabase_service.get_observations(patient_id)
    doc_obs = [o for o in obs if o.get("document_id") == document_id]
    if not doc_obs:
        doc_obs = extract_lab_observations(doc.get("summary") or "")

    abnormal_values = [o for o in doc_obs if o.get("flag") in ["high", "low", "abnormal"]]

    findings = [
        f"Extracted {len(doc_obs)} laboratory parameters from {doc['filename']}.",
        f"Document classified as {doc['document_type'].replace('_', ' ').title()}."
    ]
    if abnormal_values:
        findings.append(f"Detected {len(abnormal_values)} parameter(s) outside standard reference ranges.")

    questions = [
        "What do these findings mean for my overall health?",
        "Are any follow-up tests or medication adjustments needed?",
        "Should I make any lifestyle or dietary changes based on these results?"
    ]

    simple_exp = f"This report is a {doc['document_type'].replace('_', ' ')} uploaded on {doc.get('document_date', 'recent date')}. It records important laboratory observations."
    if abnormal_values:
        abn_names = ", ".join([a['test_name'] for a in abnormal_values[:3]])
        simple_exp += f" Note that {abn_names} parameter(s) were flagged outside typical reference limits."

    return ReportSummarizeResponse(
        document_id=document_id,
        patient_id=patient_id,
        filename=doc["filename"],
        document_type=doc["document_type"],
        simple_explanation=simple_exp,
        important_findings=findings,
        abnormal_values=abnormal_values,
        questions_for_doctor=questions
    )

@router.post("/api/reports/compare", response_model=ReportComparisonResponse)
def compare_reports(request: ReportComparisonRequest):
    """
    Report Comparison Engine.
    Compares laboratory results between two reports deterministically (numeric delta, units, status) and provides AI summary explanation.
    """
    try:
        return comparison_service.compare_reports(
            patient_id=request.patient_id,
            prev_doc_id=request.previous_document_id,
            curr_doc_id=request.current_document_id
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
