"""Unit and Integration Tests for Synthetic Patient Population Lab."""
import pytest
from fastapi.testclient import TestClient

from app.main import app, bootstrap_initial_avatars
from app.generators.population_generator import population_generator
from app.schemas.population import PopulationCohortConfig


@pytest.fixture(scope="module", autouse=True)
def init_app():
    bootstrap_initial_avatars()


@pytest.fixture
def client():
    return TestClient(app)


def test_population_cohort_generation_and_analytics():
    """Verify batch cohort generation, demographic distributions, and consistency validation."""
    cfg = PopulationCohortConfig(
        cohort_name="Test Research Cohort",
        disease_distribution={
            "wilson_disease": 3,
            "fabry_disease": 3,
            "gaucher_disease": 3
        },
        base_seed=5000
    )
    cohort = population_generator.generate_cohort(cfg)

    assert cohort.cohort_id.startswith("COHORT-")
    assert cohort.demographics_summary.total_patients == 9
    assert cohort.demographics_summary.age_mean > 0.0
    assert len(cohort.demographics_summary.disease_counts) == 3
    assert cohort.validation_summary.total_cases_validated == 9
    assert cohort.validation_summary.pass_rate >= 80.0
    assert len(cohort.roster) == 9

    # Check member records
    for m in cohort.roster:
        assert m.patient_id is not None
        assert m.disease_id in ["wilson_disease", "fabry_disease", "gaucher_disease"]
        assert m.primary_biomarker_value > 0.0


def test_population_lab_exports_and_api(client):
    """Test REST API routes and CSV/JSON export."""
    # 1. Generate via API
    gen_payload = {
        "cohort_name": "API Cohort",
        "disease_distribution": {"wilson_disease": 2, "fabry_disease": 2},
        "base_seed": 1234
    }
    resp = client.post("/api/populations/generate", json=gen_payload)
    assert resp.status_code == 200
    data = resp.json()
    c_id = data["cohort_id"]
    assert data["demographics_summary"]["total_patients"] == 4

    # 2. Get Cohort
    get_resp = client.get(f"/api/populations/cohorts/{c_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["cohort_id"] == c_id

    # 3. List Cohorts
    list_resp = client.get("/api/populations/cohorts")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 4. Export CSV
    csv_resp = client.get(f"/api/populations/cohorts/{c_id}/export?format=csv")
    assert csv_resp.status_code == 200
    assert "cohort_id,cohort_name,patient_id" in csv_resp.text

    # 5. Export JSON
    json_resp = client.get(f"/api/populations/cohorts/{c_id}/export?format=json")
    assert json_resp.status_code == 200
    assert json_resp.headers["content-type"] == "application/json"
