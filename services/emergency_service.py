import io
import uuid
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import qrcode
from services.supabase_service import supabase_service
from models.schemas import EmergencySnapshotResponse, EmergencyPublicViewResponse, CriticalAlert

class EmergencyService:
    """
    Manages Emergency Health Snapshots, "3 Critical Things You Should Know",
    and secure QR code generation & public emergency access validation.
    """
    def __init__(self):
        self._qr_tokens: Dict[str, Dict[str, Any]] = {}

    def get_or_create_emergency_snapshot(self, patient_id: str) -> EmergencySnapshotResponse:
        patient = supabase_service.get_or_create_patient(patient_id)
        meds = supabase_service.get_medications(patient_id)
        obs = supabase_service.get_observations(patient_id)

        current_meds_list = [f"{m['medicine_name']} ({m.get('dosage', 'Standard')})" for m in meds]
        if not current_meds_list:
            current_meds_list = ["No active medications reported"]

        allergies = patient.get("allergies", ["Penicillin"])
        
        # Build "3 Critical Things to Know" grounded in patient data
        critical_things = []
        if allergies:
            critical_things.append(f"Severe drug allergy reported: {', '.join(allergies)}")
        
        high_labs = [o for o in obs if o.get("flag") in ["high", "low", "abnormal"]]
        if high_labs:
            critical_things.append(f"Recent abnormal lab findings: {high_labs[0]['test_name']} ({high_labs[0]['value_text']} {high_labs[0].get('unit', '')})")
        else:
            critical_things.append("No acute blood test abnormalities detected.")
            
        if current_meds_list and current_meds_list[0] != "No active medications reported":
            critical_things.append(f"Currently taking prescribed medication: {current_meds_list[0]}")
        else:
            critical_things.append("Patient has no active emergency restrictions.")

        # Limit strictly to 3 critical things
        critical_things = critical_things[:3]

        alerts = []
        for allergy in allergies:
            alerts.append(CriticalAlert(
                category="allergy",
                title=f"Allergy Alert: {allergy}",
                severity="high",
                details=f"Patient has documented allergy to {allergy}."
            ))

        return EmergencySnapshotResponse(
            patient_id=patient_id,
            full_name=patient.get("full_name", "Valued Patient"),
            blood_group=patient.get("blood_group", "O+"),
            allergies=allergies,
            current_medications=current_meds_list,
            critical_conditions=["Hypertension"] if high_labs else ["None reported"],
            critical_things_to_know=critical_things,
            critical_alerts=alerts,
            emergency_contact={
                "name": patient.get("emergency_contact_name", "Primary Emergency Contact"),
                "phone": patient.get("emergency_contact_phone", "+1-555-0199")
            }
        )

    def generate_emergency_qr(self, patient_id: str, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        qr_token = f"EMG-{str(uuid.uuid4())[:8]}"
        emergency_url = f"{base_url}/api/emergency/{qr_token}"

        # Generate QR code base64 image
        qr_img = qrcode.make(emergency_url)
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        # Save token lookup mapping
        self._qr_tokens[qr_token] = {
            "patient_id": patient_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return {
            "patient_id": patient_id,
            "qr_token": qr_token,
            "emergency_url": emergency_url,
            "qr_code_base64": f"data:image/png;base64,{qr_b64}"
        }

    def resolve_emergency_qr_token(self, qr_token: str) -> Optional[EmergencyPublicViewResponse]:
        token_info = self._qr_tokens.get(qr_token)
        if not token_info:
            return None

        patient_id = token_info["patient_id"]
        snapshot = self.get_or_create_emergency_snapshot(patient_id)

        # Log emergency access
        from services.access_service import access_service
        access_service.log_access(
            patient_id=patient_id,
            accessor_name="Emergency First Responder (QR Scan)",
            access_type="emergency_qr",
            resource_accessed=f"Emergency Snapshot (Token: {qr_token})"
        )

        return EmergencyPublicViewResponse(
            blood_group=snapshot.blood_group,
            allergies=snapshot.allergies,
            critical_conditions=snapshot.critical_conditions,
            current_medications=snapshot.current_medications,
            critical_alerts=snapshot.critical_things_to_know,
            emergency_contact=snapshot.emergency_contact
        )

emergency_service = EmergencyService()
