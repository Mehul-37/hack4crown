from fastapi import APIRouter, HTTPException
from models.schemas import InsuranceClaimCheckRequest, InsuranceClaimCheckResponse
from services.insurance_service import insurance_service

router = APIRouter(prefix="/api/insurance", tags=["Insurance Claim Document Discovery"])

@router.post("/claims/check", response_model=InsuranceClaimCheckResponse)
def check_insurance_claim(request: InsuranceClaimCheckRequest):
    """
    Insurance Claim Document Discovery Endpoint.
    Searches patient vault against required document rules for claim submission (hospitalization, surgery, diagnostics),
    identifies ready vs missing files, and returns claim readiness score.
    """
    if not request.patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")

    return insurance_service.check_claim_readiness(
        patient_id=request.patient_id,
        claim_type=request.claim_type
    )
