from typing import List, Dict, Any
from services.supabase_service import supabase_service
from models.schemas import RequiredDocStatus, InsuranceClaimCheckResponse, DocumentInfo

CLAIM_REQUIREMENTS = {
    "hospitalization": [
        {"type": "discharge_summary", "name": "Discharge Summary"},
        {"type": "blood_report", "name": "Diagnostic / Lab Reports"},
        {"type": "prescription", "name": "Doctor Prescription"},
        {"type": "insurance_document", "name": "Government ID / Insurance Policy Copy"},
    ],
    "surgery": [
        {"type": "discharge_summary", "name": "Surgical Discharge Summary"},
        {"type": "mri_report", "name": "Pre-operative Radiology (MRI/CT/X-ray)"},
        {"type": "prescription", "name": "Post-Op Prescriptions"},
        {"type": "insurance_document", "name": "Claim Form & Insurance ID"},
    ],
    "diagnostic": [
        {"type": "blood_report", "name": "Diagnostic Lab Report"},
        {"type": "prescription", "name": "Doctor Referral Note / Prescription"},
    ]
}

class InsuranceService:
    """
    Automated insurance claim document readiness discovery.
    Identifies available vs missing documents required for insurance claim submissions.
    """
    def check_claim_readiness(self, patient_id: str, claim_type: str = "hospitalization") -> InsuranceClaimCheckResponse:
        reqs = CLAIM_REQUIREMENTS.get(claim_type.lower(), CLAIM_REQUIREMENTS["hospitalization"])
        patient_docs = supabase_service.list_documents(patient_id)

        doc_by_type: Dict[str, Dict[str, Any]] = {}
        for d in patient_docs:
            d_type = d.get("document_type", "unknown")
            if d_type not in doc_by_type:
                doc_by_type[d_type] = d

        statuses: List[RequiredDocStatus] = []
        missing_types: List[str] = []
        found_count = 0

        for r in reqs:
            req_type = r["type"]
            req_name = r["name"]
            matching_d = doc_by_type.get(req_type)

            if matching_d:
                found_count += 1
                statuses.append(RequiredDocStatus(
                    document_type=req_type,
                    required_name=req_name,
                    status="available",
                    matching_document=DocumentInfo(**matching_d)
                ))
            else:
                missing_types.append(req_name)
                statuses.append(RequiredDocStatus(
                    document_type=req_type,
                    required_name=req_name,
                    status="missing",
                    matching_document=None
                ))

        total_reqs = len(reqs)
        readiness_pct = round((found_count / total_reqs) * 100.0, 1)

        verdict = f"{found_count} of {total_reqs} required documents found in patient vault ({readiness_pct}% claim ready)."
        if missing_types:
            verdict += f" Missing: {', '.join(missing_types)}."

        return InsuranceClaimCheckResponse(
            patient_id=patient_id,
            claim_type=claim_type,
            readiness_percentage=readiness_pct,
            required_documents=statuses,
            missing_document_types=missing_types,
            summary_verdict=verdict
        )

insurance_service = InsuranceService()
