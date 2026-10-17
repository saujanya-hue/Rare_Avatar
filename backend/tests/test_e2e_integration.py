import pytest
import requests
from fastapi.testclient import TestClient
from app.main import app, bootstrap_initial_avatars

BASE_URL = "http://127.0.0.1:8000"


def _get_client_or_requests():
    try:
        r = requests.get(f"{BASE_URL}/api/patients", timeout=0.5)
        if r.status_code == 200:
            return requests
    except Exception:
        pass
    bootstrap_initial_avatars()
    tc = TestClient(app)
    class TestClientAdapter:
        @staticmethod
        def get(url, **kwargs):
            path = url.replace(BASE_URL, "")
            return tc.get(path, **kwargs)
        @staticmethod
        def post(url, **kwargs):
            path = url.replace(BASE_URL, "")
            return tc.post(path, **kwargs)
    return TestClientAdapter()


def test_e2e_api_workflow():
    client = _get_client_or_requests()
    # 1. Test listing bootstrapped patients
    r = client.get(f"{BASE_URL}/api/patients")
    assert r.status_code == 200
    patients = r.json()
    assert len(patients) >= 3

    patient = patients[0]
    pid = patient["patient_id"]

    # 2. Test Trainee View (blinded)
    r_trainee = client.get(f"{BASE_URL}/api/patients/{pid}/trainee-view")
    assert r_trainee.status_code == 200
    t_data = r_trainee.json()
    assert t_data["patient_id"] == pid
    assert "available_test_catalog" in t_data

    # 3. Test Consultation Inquiry
    r_inq = client.post(
        f"{BASE_URL}/api/simulation/inquiry",
        json={"patient_id": pid, "query_text": "Do you have any hand tremor?"}
    )
    assert r_inq.status_code == 200
    inq_data = r_inq.json()
    assert inq_data["intent_detected"] in ["SYMPTOM_EXPLORATION", "GENERAL_CHIEF_COMPLAINT"]
    assert len(inq_data["avatar_response"]) > 10

    # 4. Test Diagnostic Order
    if len(t_data["available_test_catalog"]) > 0:
        test_item = t_data["available_test_catalog"][0]
        r_order = client.post(
            f"{BASE_URL}/api/simulation/order-investigation",
            json={
                "patient_id": pid,
                "investigation_type": test_item["type"],
                "test_code_or_study_id": test_item["code"]
            }
        )
        assert r_order.status_code == 200
        assert r_order.json()["success"] is True

    # 5. Test Simulation Time Advance
    r_adv = client.post(
        f"{BASE_URL}/api/simulation/advance-time",
        json={"patient_id": pid, "advance_months": 3}
    )
    assert r_adv.status_code == 200
    assert r_adv.json()["current_month"] >= 3

    # 6. Test Validation & Privacy Audit
    r_audit = client.get(f"{BASE_URL}/api/validation/audit/{pid}")
    assert r_audit.status_code == 200
    audit_data = r_audit.json()
    assert audit_data["total_checks"] > 0
    assert audit_data["overall_privacy_risk"] == "LOW (Safe Synthetic)"

    # 7. Test Diagnostic Algorithm Stress-Testing Workflow
    r_tc = client.post(
        f"{BASE_URL}/api/diagnostic-eval/create-test-case",
        params={
            "patient_id": pid,
            "noise_sigma": 0.1,
            "missing_lab_rate": 0.2,
            "seed": 42
        }
    )
    assert r_tc.status_code == 200
    tc_data = r_tc.json()
    tc_id = tc_data["test_case_id"]

    r_eval = client.post(
        f"{BASE_URL}/api/diagnostic-eval/evaluate-baseline",
        params={"test_case_id": tc_id}
    )
    assert r_eval.status_code == 200
    eval_res = r_eval.json()
    assert "is_top1_correct" in eval_res
    assert "robustness_score" in eval_res

    # 8. Test Static Frontend Delivery
    r_fe = client.get(f"{BASE_URL}/")
    assert r_fe.status_code == 200
    assert "RareAvatar" in r_fe.text
