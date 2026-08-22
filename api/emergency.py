from fastapi import APIRouter, HTTPException, Query
from models.schemas import (
    EmergencySnapshotResponse,
    EmergencyQRRequest,
    EmergencyQRResponse,
    EmergencyPublicViewResponse
)
from services.emergency_service import emergency_service

router = APIRouter(tags=["Emergency Health Snapshot & QR"])

@router.post("/api/emergency-summary", response_model=EmergencySnapshotResponse)
@router.get("/api/emergency-summary", response_model=EmergencySnapshotResponse)
def get_or_update_emergency_summary(patient_id: str = Query(...)):
    """
    Critical Health Snapshot Endpoint.
    Generates/retrieves concise emergency profile containing blood group, allergies, current medications,
    and "3 Critical Things You Should Know".
    """
    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")

    return emergency_service.get_or_create_emergency_snapshot(patient_id)

@router.post("/api/emergency-qr", response_model=EmergencyQRResponse)
def generate_emergency_qr(request: EmergencyQRRequest):
    """
    Generate Secure Emergency Access Token & Base64 QR code.
    Points to emergency endpoint that exposes ONLY minimal emergency data.
    """
    if not request.patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")

    qr_data = emergency_service.generate_emergency_qr(request.patient_id)
    return EmergencyQRResponse(**qr_data)

@router.get("/api/emergency/{token}", response_model=EmergencyPublicViewResponse)
def get_public_emergency_view(token: str):
    """
    Public Emergency Access View (Scanned via QR Code).
    Exposes strictly minimal first-responder information (blood type, allergies, critical alerts, emergency contacts).
    Does NOT expose full medical documents or sensitive history.
    """
    snapshot = emergency_service.resolve_emergency_qr_token(token)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Invalid or expired emergency QR token")

    return snapshot
