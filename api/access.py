from typing import List
from fastapi import APIRouter, HTTPException, Query
from models.schemas import (
    AccessGrantRequest,
    AccessGrantResponse,
    AccessLogResponse,
    AccessLogItem
)
from services.access_service import access_service

router = APIRouter(tags=["Doctor Access & Privacy Audit Logs"])

@router.post("/api/access-grants", response_model=AccessGrantResponse)
def create_access_grant(request: AccessGrantRequest):
    """
    Create Timed Doctor/Hospital Access Grant.
    Generates a auto-expiring access token with customizable category permissions.
    """
    if not request.patient_id or not request.grantee_name:
        raise HTTPException(status_code=400, detail="patient_id and grantee_name are required")

    return access_service.create_access_grant(
        patient_id=request.patient_id,
        grantee_name=request.grantee_name,
        duration_hours=request.duration_hours,
        categories=request.categories
    )

@router.get("/api/access-grants", response_model=List[AccessGrantResponse])
def list_access_grants(patient_id: str = Query(...)):
    """List active, non-expired doctor access grants for patient."""
    return access_service.list_access_grants(patient_id)

@router.delete("/api/access-grants/{grant_id}")
def revoke_access_grant(grant_id: str, patient_id: str = Query(...)):
    """Immediately revoke a doctor access grant."""
    success = access_service.revoke_access_grant(grant_id, patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access grant not found or already revoked")
    return {"message": f"Access grant {grant_id} successfully revoked"}

@router.get("/api/access-logs", response_model=AccessLogResponse)
def get_access_logs(patient_id: str = Query(...)):
    """Privacy Audit Logs. Returns timestamped record of who accessed patient medical records."""
    logs = access_service.get_access_logs(patient_id)
    return AccessLogResponse(patient_id=patient_id, logs=logs)
