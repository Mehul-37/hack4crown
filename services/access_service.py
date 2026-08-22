import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from models.schemas import AccessGrantResponse, AccessLogItem

class AccessService:
    """
    Manages timed access grants for doctors/hospitals and records privacy access audit logs.
    Handles automatic expiration enforcement.
    """
    def __init__(self):
        self._grants: Dict[str, Dict[str, Any]] = {}
        self._logs: List[Dict[str, Any]] = []

    def create_access_grant(self, patient_id: str, grantee_name: str, duration_hours: int = 24, categories: List[str] = None) -> AccessGrantResponse:
        grant_id = str(uuid.uuid4())
        token = f"DOC-{str(uuid.uuid4())[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=duration_hours)

        grant = {
            "id": grant_id,
            "patient_id": patient_id,
            "grantee_name": grantee_name,
            "access_token": token,
            "expires_at": expires_at.isoformat(),
            "scope": {"categories": categories or ["all"]},
            "is_revoked": False,
            "created_at": now.isoformat()
        }

        self._grants[grant_id] = grant

        # Log creation
        self.log_access(
            patient_id=patient_id,
            accessor_name=f"Patient (Grant for {grantee_name})",
            access_type="doctor_grant",
            resource_accessed=f"Created {duration_hours}h access grant for {grantee_name}"
        )

        return AccessGrantResponse(**grant)

    def list_access_grants(self, patient_id: str) -> List[AccessGrantResponse]:
        now_str = datetime.now(timezone.utc).isoformat()
        active = []
        for g in self._grants.values():
            if g["patient_id"] == patient_id and not g["is_revoked"]:
                # Check expiration
                if g["expires_at"] > now_str:
                    active.append(AccessGrantResponse(**g))
        return active

    def revoke_access_grant(self, grant_id: str, patient_id: str) -> bool:
        if grant_id in self._grants and self._grants[grant_id]["patient_id"] == patient_id:
            self._grants[grant_id]["is_revoked"] = True
            self.log_access(
                patient_id=patient_id,
                accessor_name="Patient",
                access_type="doctor_grant",
                resource_accessed=f"Revoked access grant {grant_id}"
            )
            return True
        return False

    def validate_grant_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        now_str = datetime.now(timezone.utc).isoformat()
        for g in self._grants.values():
            if g["access_token"] == access_token and not g["is_revoked"]:
                if g["expires_at"] > now_str:
                    return g
        return None

    def log_access(self, patient_id: str, accessor_name: str, access_type: str, resource_accessed: str):
        log_entry = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "accessor_name": accessor_name,
            "access_type": access_type,
            "resource_accessed": resource_accessed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._logs.append(log_entry)

    def get_access_logs(self, patient_id: str) -> List[AccessLogItem]:
        logs = [AccessLogItem(**l) for l in self._logs if l["patient_id"] == patient_id]
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs

access_service = AccessService()
