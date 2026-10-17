"""Unit and Integration Tests for Clinical Consistency Guardian."""
import pytest
from fastapi.testclient import TestClient

from app.main import app, bootstrap_initial_avatars
from app.generators.patient_generator import patient_generator
from app.validation.consistency_checker import consistency_checker
from app.schemas.validation import ComprehensiveValidationReport


@pytest.fixture(scope="module", autouse=True)
def init_app():
    bootstrap_initial_avatars()


@pytest.fixture
def client():
    return TestClient(app)


def test_consistency_guardian_all_diseases_valid():
    """Verify that pristine avatars for all 3 supported diseases pass consistency guardian checks."""
    for d_id in ["wilson_disease", "fabry_disease", "gaucher_disease"]:
        patient = patient_generator.generate_patient(disease_id=d_id, seed=100)
        results = consistency_checker.validate_patient(patient)

        # Must have evaluations across multiple categories
        categories = {r.category for r in results}
        assert "PHYSIOLOGICAL" in categories
        assert "CROSS_MODAL" in categories
        assert "TEMPORAL" in categories
        assert "TREATMENT_MODEL" in categories
        assert "EVIDENCE_GROUNDING" in categories

        # No fatal errors on pristine baseline avatars
        fatal_errors = [r for r in results if not r.passed and r.severity == "FATAL_ERROR"]
        assert len(fatal_errors) == 0, f"Fatal errors on {d_id}: {[r.details for r in fatal_errors]}"

        # Category summary
        summary = consistency_checker.compute_category_summary(results)
        for cat in ["PHYSIOLOGICAL", "CROSS_MODAL", "TEMPORAL", "TREATMENT_MODEL", "EVIDENCE_GROUNDING"]:
            assert cat in summary
            assert summary[cat]["total"] > 0
            assert summary[cat]["failed"] == 0

        verdict = consistency_checker.determine_guardian_verdict(results)
        assert verdict in ["FULL_CLINICAL_CONCORDANCE", "MINOR_DISCREPANCIES_DETECTED"]


def test_consistency_guardian_catches_cross_modal_fabry():
    """Verify that discordant enzyme vs substrate biomarker triggers cross-modal rule failure."""
    patient = patient_generator.generate_patient(disease_id="fabry_disease", seed=42)

    # Set normal/high alpha-gal A with high Lyso-Gb3 (pathophysiologically incoherent)
    for lab in patient.lab_history:
        if lab.test_code in ["ALPHA_GALACTOSIDASE_A", "ALPHA_GAL_A"]:
            lab.value = 14.0  # Normal/high activity
        if lab.test_code == "LYSO_GB3":
            lab.value = 25.0  # Markedly elevated

    results = consistency_checker.validate_patient(patient)
    xm_fail = [r for r in results if r.rule_id == "XMODAL_FD_ENZYME_BIOMARKER_SYNC" and not r.passed]
    assert len(xm_fail) == 1
    assert xm_fail[0].severity == "FATAL_ERROR"
    assert "Alpha-Gal A" in xm_fail[0].details or "Alpha-Gal A" in xm_fail[0].observed_value


def test_consistency_guardian_catches_temporal_anomaly():
    """Verify that negative onset month or onset exceeding age is flagged."""
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    patient.symptoms[0].onset_month = -12  # Impossible negative onset

    results = consistency_checker.validate_patient(patient)
    temp_fail = [r for r in results if r.category == "TEMPORAL" and not r.passed]
    assert len(temp_fail) >= 1
    assert any(r.severity == "FATAL_ERROR" for r in temp_fail)


def test_consistency_guardian_api_audit_and_validate(client):
    """Test REST API routes for audit and validate-case."""
    # 1. Audit active patient
    resp = client.get("/api/patients")
    patients = resp.json()
    assert len(patients) > 0
    p_id = patients[0]["patient_id"]

    audit_resp = client.get(f"/api/validation/audit/{p_id}")
    assert audit_resp.status_code == 200
    report = audit_resp.json()
    assert report["patient_id"] == p_id
    assert "guardian_verdict" in report
    assert "category_summary" in report
    assert "PHYSIOLOGICAL" in report["category_summary"]
    assert "CROSS_MODAL" in report["category_summary"]

    # 2. Validate custom case via POST
    full_resp = client.get(f"/api/patients/{p_id}")
    full_patient = full_resp.json()

    post_resp = client.post("/api/validation/validate-case", json=full_patient)
    assert post_resp.status_code == 200
    post_report = post_resp.json()
    assert post_report["patient_id"] == p_id
    assert post_report["total_checks"] > 0
