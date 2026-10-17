"""Unit and integration tests for Authentication and Trainee/Supervisor Role Management."""
import pytest
from fastapi.testclient import TestClient
from app.main import app, bootstrap_initial_avatars

client = TestClient(app)
bootstrap_initial_avatars()


def test_trainee_login_success():
    """Verify trainee login requires and accepts Trainee ID with @ggmail.com."""
    response = client.post("/api/auth/login", json={
        "email": "TR-8041@ggmail.com",
        "role": "trainee"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["role"] == "trainee"
    assert data["user"]["user_id"] == "TR-8041"
    assert "view_blinded_workspace" in data["user"]["permissions"]


def test_trainee_login_rejects_non_ggmail():
    """Verify trainee login rejects emails not ending in @ggmail.com."""
    response = client.post("/api/auth/login", json={
        "email": "trainee_123@othermail.com",
        "role": "trainee"
    })
    assert response.status_code == 400
    assert "@ggmail.com" in response.json()["detail"]


def test_supervisor_login_success():
    """Verify supervisor login succeeds and unlocks supervisor permissions."""
    response = client.post("/api/auth/login", json={
        "email": "SUP-001@ggmail.com",
        "role": "supervisor"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["role"] == "supervisor"
    assert data["user"]["user_id"] == "SUP-001"
    assert "run_adversarial_arena" in data["user"]["permissions"]
    assert "full_ground_truth_access" in data["user"]["permissions"]


def test_trainee_submit_diagnosis_evaluation():
    """Verify trainee diagnostic submission compares against ground truth and scores hallmarks."""
    # Ensure a patient avatar exists
    patients_resp = client.get("/api/patients")
    assert patients_resp.status_code == 200
    patients = patients_resp.json()
    assert len(patients) > 0
    patient = patients[0]
    pid = patient["patient_id"]

    submission = {
        "patient_id": pid,
        "trainee_id": "TR-8041",
        "trainee_email": "TR-8041@ggmail.com",
        "primary_diagnosis": patient["disease_name"],
        "differential_diagnoses": ["Hemochromatosis", "Autoimmune Hepatitis"],
        "clinical_justification": "Patient exhibited low ceruloplasmin, elevated copper, and hepatic transaminitis.",
        "months_elapsed": 6,
        "ordered_investigations": ["Serum Ceruloplasmin", "24-Hour Urinary Copper Excretion", "Slit-Lamp Examination"]
    }

    sub_resp = client.post("/api/auth/trainee-submit-diagnosis", json=submission)
    assert sub_resp.status_code == 200
    result = sub_resp.json()
    assert result["is_correct"] is True
    assert result["accuracy_score"] >= 90.0
    assert result["trainee_id"] == "TR-8041"
    assert "supervisor_debriefing" in result


def test_supervisor_trainee_records():
    """Verify supervisor can query aggregate trainee performance records."""
    resp = client.get("/api/auth/supervisor/trainee-records")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "submissions" in data
    assert data["summary"]["total_trainee_submissions"] >= 3
    assert data["summary"]["overall_pass_rate_pct"] > 0
