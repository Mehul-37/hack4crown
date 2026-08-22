from typing import List
from fastapi import APIRouter, HTTPException
from services.supabase_service import supabase_service
from models.schemas import TimelineEventSchema

router = APIRouter(prefix="/api/timeline", tags=["Health Timeline"])

@router.get("", response_model=List[TimelineEventSchema])
def get_patient_timeline(patient_id: str):
    """
    Chronological Health Timeline.
    Returns structured health events (blood tests, consultations, prescriptions, scans, surgeries) sorted by date.
    Does not require expensive real-time LLM re-computation on page view.
    """
    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")

    events = supabase_service.get_timeline(patient_id)
    return [TimelineEventSchema(**e) for e in events]
