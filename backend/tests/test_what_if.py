"""Unit and Integration Tests for Clinical What-If Lab."""
import pytest
from fastapi.testclient import TestClient

from app.main import app, bootstrap_initial_avatars
from app.engine.what_if_engine import what_if_engine
from app.schemas.simulation import WhatIfBranchConfig, WhatIfAdvanceBranchRequest, WhatIfComparisonRequest


@pytest.fixture(scope="module", autouse=True)
def init_app():
    bootstrap_initial_avatars()


@pytest.fixture
def client():
    return TestClient(app)


def test_what_if_branch_creation_and_isolation(client):
    """Verify that branching creates an independent, isolated simulation branch."""
    p_resp = client.get("/api/patients")
    patients = p_resp.json()
    p_id = patients[0]["patient_id"]

    cfg = WhatIfBranchConfig(
        patient_id=p_id,
        branch_name="Early Targeted Chelation",
        intervention_type="Targeted Therapy",
        intervention_agent="D-Penicillamine",
        origin_month=0
    )
    branch = what_if_engine.create_branch(cfg)

    assert branch.branch_id.startswith("BRANCH-")
    assert branch.patient_id == p_id
    assert len(branch.trajectory) == 1
    assert branch.trajectory[0].month == 0


def test_what_if_branch_advancement_and_comparison(client):
    """Verify advancement of branches and side-by-side multi-branch comparison."""
    p_resp = client.get("/api/patients")
    p_id = p_resp.json()[0]["patient_id"]

    # 1. Create Treated Branch
    b1 = what_if_engine.create_branch(WhatIfBranchConfig(
        patient_id=p_id,
        branch_name="Branch A: First-Line Therapy",
        intervention_type="Targeted Therapy",
        intervention_agent="D-Penicillamine"
    ))

    # 2. Create Untreated Natural History Branch
    b2 = what_if_engine.create_branch(WhatIfBranchConfig(
        patient_id=p_id,
        branch_name="Branch B: Untreated Natural History",
        intervention_type="Untreated Natural History",
        intervention_agent="Untreated"
    ))

    # Advance both branches by 12 months
    adv1 = what_if_engine.advance_branch(b1.branch_id, advance_months=12)
    adv2 = what_if_engine.advance_branch(b2.branch_id, advance_months=12)

    assert adv1.current_month == 12
    assert adv2.current_month == 12
    assert len(adv1.trajectory) >= 2
    assert len(adv2.trajectory) >= 2

    # Compare branches
    report = what_if_engine.compare_branches(p_id, [b1.branch_id, b2.branch_id])
    assert report.comparison_id.startswith("WICMP-")
    assert len(report.comparative_metrics) == 2
    assert len(report.clinical_recommendation) > 0


def test_what_if_api_routes(client):
    """Test REST API routes for What-If Lab."""
    p_resp = client.get("/api/patients")
    p_id = p_resp.json()[0]["patient_id"]

    # Create via API
    create_payload = {
        "patient_id": p_id,
        "branch_name": "API Test Branch",
        "intervention_type": "Targeted Therapy",
        "intervention_agent": "D-Penicillamine",
        "origin_month": 0
    }
    resp = client.post("/api/what-if/branches/create", json=create_payload)
    assert resp.status_code == 200
    b_data = resp.json()
    b_id = b_data["branch_id"]

    # Advance via API
    adv_resp = client.post("/api/what-if/branches/advance", json={"branch_id": b_id, "advance_months": 6})
    assert adv_resp.status_code == 200
    adv_data = adv_resp.json()
    assert adv_data["current_month"] == 6

    # List branches for patient
    list_resp = client.get(f"/api/what-if/branches/patient/{p_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Export CSV
    csv_resp = client.get(f"/api/what-if/branches/{b_id}/export")
    assert csv_resp.status_code == 200
    assert "branch_id,branch_name" in csv_resp.text
