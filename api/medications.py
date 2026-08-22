from typing import List
from fastapi import APIRouter, HTTPException
from services.supabase_service import supabase_service
from models.schemas import MedicationSchema

router = APIRouter(prefix="/api/medications", tags=["Medications"])

@router.get("", response_model=List[MedicationSchema])
def get_patient_medications(patient_id: str):
    """
    Structured Medication Intelligence.
    Returns active and historical medication records extracted from prescriptions and clinical documents.
    """
    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")

    meds = supabase_service.get_medications(patient_id)
    return [MedicationSchema(**m) for m in meds]
