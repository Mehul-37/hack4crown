import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_document_upload_txt():
    txt_content = b"Patient John Doe. Blood Test Date: 2026-08-15. Hemoglobin: 11.8 g/dL. Vitamin D: 22 ng/mL. Atorvastatin 10 mg daily."
    file_tuple = ("blood_report.txt", io.BytesIO(txt_content), "text/plain")

    response = client.post(
        "/api/documents/upload",
        data={"patient_id": "patient_A"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == "patient_A"
    assert data["document_type"] == "blood_report"
    assert data["observations_extracted"] >= 1
    assert data["medications_extracted"] >= 1
    assert data["chunks_created"] >= 1

def test_patient_data_isolation():
    # Upload document for patient A
    txt_a = b"Patient A Medical History. Hemoglobin: 14.5 g/dL. Diagnosis: Mild asthma."
    res_a = client.post("/api/documents/upload", data={"patient_id": "patient_A"}, files={"file": ("doc_a.txt", io.BytesIO(txt_a), "text/plain")})
    assert res_a.status_code == 201
    doc_a_id = res_a.json()["document_id"]

    # Upload document for patient B
    txt_b = b"Patient B Confidential Record. Hemoglobin: 9.2 g/dL. Diagnosis: Severe Anemia."
    res_b = client.post("/api/documents/upload", data={"patient_id": "patient_B"}, files={"file": ("doc_b.txt", io.BytesIO(txt_b), "text/plain")})
    assert res_b.status_code == 201
    doc_b_id = res_b.json()["document_id"]

    # Query Patient A documents list
    list_a = client.get("/api/documents?patient_id=patient_A").json()
    patient_a_doc_ids = [d["id"] for d in list_a["documents"]]
    assert doc_a_id in patient_a_doc_ids
    assert doc_b_id not in patient_a_doc_ids

    # Query RAG Chat as Patient A asking for hemoglobin
    chat_a = client.post("/api/chat", json={"patient_id": "patient_A", "question": "What is my hemoglobin?"}).json()
    assert chat_a["patient_id"] == "patient_A"
    # Ensure source citations only contain Patient A documents
    for src in chat_a["sources"]:
        assert src["document_id"] != doc_b_id

def test_rag_chat_citations():
    # Upload prescription document for patient_C
    txt_rx = b"Prescription Record Date: 2026-08-20. Patient taking Metformin 500mg once daily and Atorvastatin 10mg daily."
    up_res = client.post("/api/documents/upload", data={"patient_id": "patient_C"}, files={"file": ("rx_record.txt", io.BytesIO(txt_rx), "text/plain")})
    assert up_res.status_code == 201

    chat_res = client.post("/api/chat", json={
        "patient_id": "patient_C",
        "question": "What medications am I taking?"
    })
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "answer" in data
    assert len(data["sources"]) > 0
    assert "rx_record.txt" in data["sources"][0]["filename"]

def test_report_comparison():
    # Upload previous report
    txt_prev = b"Blood Test Date: 2026-01-10. Hemoglobin: 13.4 g/dL."
    res_prev = client.post("/api/documents/upload", data={"patient_id": "patient_A"}, files={"file": ("jan_report.txt", io.BytesIO(txt_prev), "text/plain")})
    prev_id = res_prev.json()["document_id"]

    # Upload current report
    txt_curr = b"Blood Test Date: 2026-08-20. Hemoglobin: 12.1 g/dL."
    res_curr = client.post("/api/documents/upload", data={"patient_id": "patient_A"}, files={"file": ("aug_report.txt", io.BytesIO(txt_curr), "text/plain")})
    curr_id = res_curr.json()["document_id"]

    comp_res = client.post("/api/reports/compare", json={
        "patient_id": "patient_A",
        "previous_document_id": prev_id,
        "current_document_id": curr_id
    })
    assert comp_res.status_code == 200
    data = comp_res.json()
    assert len(data["metrics"]) >= 1
    hb_metric = [m for m in data["metrics"] if m["parameter"] == "Hemoglobin"][0]
    assert hb_metric["previous_value"] == 13.4
    assert hb_metric["current_value"] == 12.1
    assert hb_metric["change_delta"] == -1.3
    assert hb_metric["status"] == "decreased"

def test_health_timeline():
    res = client.get("/api/timeline?patient_id=patient_A")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
    assert len(events) >= 1

def test_emergency_snapshot_and_qr():
    # Generate Emergency Summary
    summary_res = client.post("/api/emergency-summary?patient_id=patient_A")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert "critical_things_to_know" in summary_data
    assert len(summary_data["critical_things_to_know"]) <= 3

    # Generate Emergency QR
    qr_res = client.post("/api/emergency-qr", json={"patient_id": "patient_A"})
    assert qr_res.status_code == 200
    qr_data = qr_res.json()
    assert "qr_token" in qr_data
    assert "qr_code_base64" in qr_data

    # Test Public View via QR token
    pub_res = client.get(f"/api/emergency/{qr_data['qr_token']}")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert "blood_group" in pub_data
    assert "critical_alerts" in pub_data

def test_doctor_access_grants():
    grant_res = client.post("/api/access-grants", json={
        "patient_id": "patient_A",
        "grantee_name": "Dr. Sharma",
        "duration_hours": 24
    })
    assert grant_res.status_code == 200
    grant_data = grant_res.json()
    assert grant_data["grantee_name"] == "Dr. Sharma"
    grant_id = grant_data["id"]

    # List active grants
    list_res = client.get("/api/access-grants?patient_id=patient_A")
    assert list_res.status_code == 200
    grants = list_res.json()
    assert any(g["id"] == grant_id for g in grants)

    # Revoke grant
    del_res = client.delete(f"/api/access-grants/{grant_id}?patient_id=patient_A")
    assert del_res.status_code == 200

def test_insurance_claim_check():
    res = client.post("/api/insurance/claims/check", json={
        "patient_id": "patient_A",
        "claim_type": "hospitalization"
    })
    assert res.status_code == 200
    data = res.json()
    assert "readiness_percentage" in data
    assert "required_documents" in data

def test_document_deletion_cascading():
    # Upload document to delete
    txt = b"Temp report to delete. Blood Test: Glucose 95 mg/dL."
    res = client.post("/api/documents/upload", data={"patient_id": "patient_A"}, files={"file": ("to_delete.txt", io.BytesIO(txt), "text/plain")})
    doc_id = res.json()["document_id"]

    # Delete document
    del_res = client.delete(f"/api/documents/{doc_id}?patient_id=patient_A")
    assert del_res.status_code == 200

    # Verify not found in document details
    get_res = client.get(f"/api/documents/{doc_id}?patient_id=patient_A")
    assert get_res.status_code == 404

def test_document_upload_image_prescription():
    # Generate a dummy 100x100 RGB image simulating a handwritten prescription file
    img = Image.new('RGB', (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    res = client.post(
        "/api/documents/upload",
        data={"patient_id": "patient_A"},
        files={"file": ("rx_handwritten.jpg", buf, "image/jpeg")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["patient_id"] == "patient_A"
    assert "document_id" in data

