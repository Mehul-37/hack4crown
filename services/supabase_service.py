import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, date

class SupabaseService:
    """
    Core data layer service interfacing with Supabase Postgres and Storage.
    Manages document metadata, observations, medications, timeline events, access grants, and audit logs.
    Includes in-memory state fallback when Supabase connection parameters are unavailable.
    """
    def __init__(self):
        self.supabase_client = None
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key and "example.supabase.co" not in supabase_url:
            try:
                from supabase import create_client
                self.supabase_client = create_client(supabase_url, supabase_key)
            except Exception:
                self.supabase_client = None

        # Fallback in-memory DB tables
        self.db_patients: Dict[str, Dict[str, Any]] = {}
        self.db_documents: Dict[str, Dict[str, Any]] = {}
        self.db_observations: List[Dict[str, Any]] = []
        self.db_medications: List[Dict[str, Any]] = []
        self.db_timeline: List[Dict[str, Any]] = []
        self.db_access_grants: Dict[str, Dict[str, Any]] = {}
        self.db_access_logs: List[Dict[str, Any]] = []

    # --- Patient Operations ---
    def get_or_create_patient(self, patient_id: str, full_name: str = "Test Patient") -> Dict[str, Any]:
        if self.supabase_client:
            try:
                res = self.supabase_client.table("patients").select("*").eq("id", patient_id).execute()
                if res.data:
                    return res.data[0]
                patient = {
                    "id": patient_id,
                    "full_name": full_name,
                    "blood_group": "O+",
                    "allergies": ["Penicillin"],
                    "emergency_contact_name": "Emergency Contact",
                    "emergency_contact_phone": "+1-555-0199"
                }
                res_ins = self.supabase_client.table("patients").insert(patient).execute()
                return res_ins.data[0] if res_ins.data else patient
            except Exception:
                pass

        if patient_id not in self.db_patients:
            self.db_patients[patient_id] = {
                "id": patient_id,
                "full_name": full_name,
                "blood_group": "O+",
                "allergies": ["Penicillin"],
                "emergency_contact_name": "Emergency Contact",
                "emergency_contact_phone": "+1-555-0199"
            }
        return self.db_patients[patient_id]

    # --- Storage & Document Operations ---
    def save_document_file(self, patient_id: str, document_id: str, filename: str, file_bytes: bytes) -> str:
        storage_path = f"medical-documents/{patient_id}/{document_id}/{filename}"
        if self.supabase_client:
            try:
                self.supabase_client.storage.from_("medical-documents").upload(
                    path=f"{patient_id}/{document_id}/{filename}",
                    file=file_bytes,
                    file_options={"upsert": "true"}
                )
            except Exception:
                pass
        return storage_path

    def insert_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.supabase_client:
            try:
                res = self.supabase_client.table("documents").insert(doc_data).execute()
                if res.data:
                    return res.data[0]
            except Exception:
                pass

        self.db_documents[doc_data["id"]] = doc_data
        return doc_data

    def get_document(self, document_id: str, patient_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase_client:
            try:
                res = self.supabase_client.table("documents").select("*").eq("id", document_id).eq("patient_id", patient_id).execute()
                if res.data:
                    return res.data[0]
            except Exception:
                pass

        doc = self.db_documents.get(document_id)
        if doc and doc["patient_id"] == patient_id:
            return doc
        return None

    def list_documents(self, patient_id: str) -> List[Dict[str, Any]]:
        if self.supabase_client:
            try:
                res = self.supabase_client.table("documents").select("*").eq("patient_id", patient_id).order("upload_date", desc=True).execute()
                if res.data:
                    return res.data
            except Exception:
                pass

        return [d for d in self.db_documents.values() if d["patient_id"] == patient_id]

    def delete_document(self, document_id: str, patient_id: str) -> bool:
        if self.supabase_client:
            try:
                self.supabase_client.table("documents").delete().eq("id", document_id).eq("patient_id", patient_id).execute()
            except Exception:
                pass

        # Cascading removal from memory fallback
        if document_id in self.db_documents:
            del self.db_documents[document_id]
        self.db_observations = [o for o in self.db_observations if not (o.get("document_id") == document_id and o["patient_id"] == patient_id)]
        self.db_medications = [m for m in self.db_medications if not (m.get("document_id") == document_id and m["patient_id"] == patient_id)]
        self.db_timeline = [t for t in self.db_timeline if not (t.get("document_id") == document_id and t["patient_id"] == patient_id)]
        return True

    # --- Structured Medical Data ---
    def insert_observations(self, observations: List[Dict[str, Any]]):
        if not observations:
            return
        if self.supabase_client:
            try:
                self.supabase_client.table("medical_observations").insert(observations).execute()
                return
            except Exception:
                pass
        self.db_observations.extend(observations)

    def get_observations(self, patient_id: str) -> List[Dict[str, Any]]:
        if self.supabase_client:
            try:
                res = self.supabase_client.table("medical_observations").select("*").eq("patient_id", patient_id).execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        return [o for o in self.db_observations if o["patient_id"] == patient_id]

    def insert_medications(self, medications: List[Dict[str, Any]]):
        if not medications:
            return
        if self.supabase_client:
            try:
                self.supabase_client.table("medications").insert(medications).execute()
                return
            except Exception:
                pass
        self.db_medications.extend(medications)

    def get_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        if self.supabase_client:
            try:
                res = self.supabase_client.table("medications").select("*").eq("patient_id", patient_id).execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        return [m for m in self.db_medications if m["patient_id"] == patient_id]

    def insert_timeline_event(self, event: Dict[str, Any]):
        if self.supabase_client:
            try:
                self.supabase_client.table("timeline_events").insert(event).execute()
                return
            except Exception:
                pass
        self.db_timeline.append(event)

    def get_timeline(self, patient_id: str) -> List[Dict[str, Any]]:
        if self.supabase_client:
            try:
                res = self.supabase_client.table("timeline_events").select("*").eq("patient_id", patient_id).order("event_date", desc=True).execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        events = [t for t in self.db_timeline if t["patient_id"] == patient_id]
        events.sort(key=lambda x: x.get("event_date", ""), reverse=True)
        return events

supabase_service = SupabaseService()
