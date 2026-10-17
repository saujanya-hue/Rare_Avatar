"""Unit and Integration Tests for Clinical Mystery Mode."""
import pytest
from fastapi.testclient import TestClient

from app.main import app, bootstrap_initial_avatars
from app.engine.mystery_manager import mystery_manager
from app.schemas.mystery import (
    MysterySessionConfig, MysteryInvestigationOrderRequest,
    MysteryInquiryRequest, MysterySubmissionRequest
)


@pytest.fixture(scope="module", autouse=True)
def init_app():
    bootstrap_initial_avatars()


@pytest.fixture
def client():
    return TestClient(app)


def test_mystery_session_lifecycle():
    """Verify full end-to-end lifecycle of a mystery clinical diagnostic challenge."""
    # 1. Start Mystery Session (Beginner)
    cfg = MysterySessionConfig(
        difficulty="beginner",
        disease_selection="wilson_disease",
        trainee_id="TR-8041",
        random_seed=42
    )
    view = mystery_manager.start_session(cfg)

    assert view.session_id.startswith("MYS-")
    assert view.trainee_id == "TR-8041"
    assert view.status == "IN_PROGRESS"
    assert len(view.chief_complaint) > 0
    assert view.accumulated_cost_usd == 0.0

    # 2. Inquiry Dialogue
    inq_resp = mystery_manager.process_inquiry(MysteryInquiryRequest(
        session_id=view.session_id,
        query_text="Do you have any hand tremors or difficulty writing?"
    ))
    assert "avatar_response" in inq_resp
    assert inq_resp["session_id"] == view.session_id

    # 3. Order Investigation (Ceruloplasmin)
    inv_item = mystery_manager.order_investigation(MysteryInvestigationOrderRequest(
        session_id=view.session_id,
        investigation_type="lab",
        code_or_acronym="CERULOPLASMIN"
    ))
    assert inv_item.code_or_acronym == "CERULOPLASMIN"
    assert inv_item.simulated_cost_usd > 0
    assert view.accumulated_cost_usd >= 65.0

    # 4. Submit Final Diagnosis (Correct)
    sub = MysterySubmissionRequest(
        session_id=view.session_id,
        predicted_disease_id="wilson_disease",
        predicted_disease_name="Wilson Disease",
        confidence_score=0.92,
        differential_diagnoses=[{"Wilson Disease": 0.92}, {"Fabry Disease": 0.05}],
        clinical_justification="Patient presents with prominent tremor and ceruloplasmin deficiency."
    )
    report = mystery_manager.submit_diagnosis(sub)

    assert report.session_id == view.session_id
    assert report.ground_truth_disease_id == "wilson_disease"
    assert report.scorecard.is_top1_correct is True
    assert report.scorecard.overall_clinical_score >= 70.0
    assert report.debriefing.correct_disease_name is not None
    assert len(report.debriefing.pathognomonic_findings) > 0


def test_mystery_mode_api_endpoints(client):
    """Test REST API routes for Clinical Mystery Mode."""
    # Start via API
    start_payload = {
        "difficulty": "intermediate",
        "disease_selection": "fabry_disease",
        "trainee_id": "TR-8041",
        "random_seed": 77
    }
    resp = client.post("/api/mystery/start", json=start_payload)
    assert resp.status_code == 200
    view_data = resp.json()
    sess_id = view_data["session_id"]

    # Order test via API
    ord_resp = client.post("/api/mystery/order", json={
        "session_id": sess_id,
        "investigation_type": "lab",
        "code_or_acronym": "LYSO_GB3"
    })
    assert ord_resp.status_code == 200
    inv = ord_resp.json()
    assert inv["code_or_acronym"] == "LYSO_GB3"

    # Submit via API
    sub_payload = {
        "session_id": sess_id,
        "predicted_disease_id": "fabry_disease",
        "predicted_disease_name": "Fabry Disease",
        "confidence_score": 0.88,
        "differential_diagnoses": [{"Fabry Disease": 0.88}],
        "clinical_justification": "Elevated Lyso-Gb3 confirming glycosphingolipid storage disease."
    }
    sub_resp = client.post("/api/mystery/submit", json=sub_payload)
    assert sub_resp.status_code == 200
    rep = sub_resp.json()
    assert rep["ground_truth_disease_id"] == "fabry_disease"
    assert rep["scorecard"]["is_top1_correct"] is True

    # Supervisor sessions list
    sup_resp = client.get("/api/mystery/supervisor/sessions")
    assert sup_resp.status_code == 200
    sessions_list = sup_resp.json()
    assert len(sessions_list) >= 1
