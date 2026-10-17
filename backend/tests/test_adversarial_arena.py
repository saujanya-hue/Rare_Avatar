"""Unit and Integration Tests for Diagnostic AI Adversarial Arena.

Tests verify:
- Deterministic patient scenario generation with fixed seeds
- Constraint-aware perturbations and transformation tracking
- Hard constraint validation and case rejection
- Separation of blinded model inputs from ground truth reference labels
- Baseline vs. perturbed diagnostic evaluation
- Failure mode classification (INCORRECT_PREDICTION, PREDICTION_INSTABILITY, CONFIDENCE_COLLAPSE, CONSTRAINT_VIOLATION, UNEVALUABLE)
- Mathematically sound benchmark metrics (exact denominators, degradation, instability)
- Mock external diagnostic model integration, error, and timeout handling
- Experiment reproducibility and export (JSON & CSV)
- API endpoint contracts and validation
"""
import json
import pytest
import requests
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app, bootstrap_initial_avatars
from app.schemas.diagnostic import (
    PerturbationConfig, ArenaExperimentConfig, ExportableTestCase,
    DiagnosticPredictionResult
)
from app.generators.patient_generator import patient_generator
from app.stress_testing.perturbation_engine import perturbation_engine
from app.stress_testing.adversarial_arena import (
    adversarial_arena_engine, MockFragileDiagnosticClassifier, MockRobustDiagnosticClassifier
)


@pytest.fixture(scope="module", autouse=True)
def init_app_state():
    bootstrap_initial_avatars()


@pytest.fixture
def test_client():
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. Deterministic Scenario Generation with Fixed Seed
# -----------------------------------------------------------------------------
def test_deterministic_patient_generation():
    pt1 = patient_generator.generate_patient(disease_id="wilson_disease", seed=12345)
    pt2 = patient_generator.generate_patient(disease_id="wilson_disease", seed=12345)

    assert pt1.patient_id == pt2.patient_id
    assert pt1.demographics.age_years == pt2.demographics.age_years
    assert pt1.demographics.biological_sex == pt2.demographics.biological_sex
    assert len(pt1.symptoms) == len(pt2.symptoms)
    assert len(pt1.lab_history) == len(pt2.lab_history)
    for l1, l2 in zip(pt1.lab_history, pt2.lab_history):
        assert l1.test_code == l2.test_code
        assert l1.value == l2.value


# -----------------------------------------------------------------------------
# 2. Perturbation Engine & Transformation Tracking
# -----------------------------------------------------------------------------
def test_perturbation_transformation_tracking():
    patient = patient_generator.generate_patient(disease_id="fabry_disease", seed=42)
    cfg = PerturbationConfig(
        noise_sigma=0.15,
        missing_lab_rate=0.3,
        atypical_age_shift_years=10,
        inject_confounding_infection=True,
        reproducibility_seed=777
    )

    arena_case = perturbation_engine.create_arena_case(patient, cfg, experiment_id="EXP-TEST")

    # Check transformations recorded
    trans = arena_case["applied_transformations"]
    assert len(trans) > 0

    trans_types = {t.transformation_type for t in trans}
    assert "ATYPICAL_AGE_SHIFT" in trans_types
    assert "CONFOUNDING_INFECTION" in trans_types

    # Verify age shift transformation record
    age_t = next(t for t in trans if t.transformation_type == "ATYPICAL_AGE_SHIFT")
    assert age_t.original_value == patient.demographics.age_years
    assert age_t.perturbed_value == patient.demographics.age_years + 10

    # Verify blinded inputs structure
    blinded = arena_case["blinded_inputs"]
    assert "demographics" in blinded
    assert "symptoms" in blinded
    assert "laboratory" in blinded
    assert "imaging_summary" in blinded


# -----------------------------------------------------------------------------
# 3. Reference-Label Isolation (Blinded Inputs never expose Ground Truth)
# -----------------------------------------------------------------------------
def test_reference_label_isolation():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=555)
    cfg = PerturbationConfig(noise_sigma=0.1, missing_lab_rate=0.0, reproducibility_seed=101)

    arena_case = perturbation_engine.create_arena_case(patient, cfg, experiment_id="EXP-ISO")
    blinded = arena_case["blinded_inputs"]

    # Demographics must NOT contain disease names
    demo_str = json.dumps(blinded["demographics"]).lower()
    assert "wilson" not in demo_str
    assert "disease" not in demo_str

    # Laboratory tests must not contain ground truth disease
    labs_str = json.dumps(blinded["laboratory"]).lower()
    assert "wilson" not in labs_str

    # Imaging findings must not contain definitive disease label
    img_str = json.dumps(blinded["imaging_summary"]).lower()
    assert "wilson" not in img_str

    # Exportable test case must cleanly separate input from ground truth
    tc = arena_case["exportable_test_case"]
    assert tc.ground_truth_disease_id == "wilson_disease"
    assert "wilson" not in str(tc.input_demographics).lower()


# -----------------------------------------------------------------------------
# 4. Constraint Violations & Rejection of Medically Impossible Patients
# -----------------------------------------------------------------------------
def test_hard_constraint_violation_detection():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=888)

    # In Wilson disease, Ceruloplasmin upper bound is <= 20.0 mg/dL (FATAL_ERROR)
    # If massive noise or impossible perturbation pushes ceruloplasmin above 20.0, it must be flagged
    cp_lab = next(l for l in patient.lab_history if l.test_code == "CERULOPLASMIN")
    orig_val = cp_lab.value

    # Temporarily force value to violate hard constraint
    cp_lab.value = 35.0  # Medically inconsistent with classical active Wilson disease

    cfg = PerturbationConfig(noise_sigma=0.0, missing_lab_rate=0.0, reproducibility_seed=42)
    arena_case = perturbation_engine.create_arena_case(patient, cfg, experiment_id="EXP-VIOLATION")

    c_status = arena_case["constraint_validation"]
    assert c_status.is_valid is False
    assert c_status.status == "VIOLATED"
    assert any("CERULOPLASMIN" in v for v in c_status.violations)

    # Restore clean value
    cp_lab.value = orig_val


# -----------------------------------------------------------------------------
# 5. Diagnostic Model Evaluation (Baseline vs Fragile vs Robust)
# -----------------------------------------------------------------------------
def test_baseline_and_fragile_classifier_behavior():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=1001)

    # Baseline unperturbed case
    b_cfg = PerturbationConfig(noise_sigma=0.0, missing_lab_rate=0.0, reproducibility_seed=1001)
    b_case = perturbation_engine.create_arena_case(patient, b_cfg)["exportable_test_case"]

    # Reference baseline classifier
    base_res = adversarial_arena_engine.evaluate_model("reference_baseline", b_case)
    assert base_res.is_top1_correct is True
    assert base_res.predicted_disease_id == "wilson_disease"

    # Perturbed case with confounding acute infection
    p_cfg = PerturbationConfig(
        noise_sigma=0.05,
        missing_lab_rate=0.0,
        inject_confounding_infection=True,
        reproducibility_seed=1001
    )
    p_case = perturbation_engine.create_arena_case(patient, p_cfg)["exportable_test_case"]

    # Fragile classifier is tricked by acute infection confounder into misdiagnosis
    fragile_res = adversarial_arena_engine.evaluate_model("mock_fragile", p_case)
    assert fragile_res.is_top1_correct is False
    assert fragile_res.predicted_disease_id == "other_idiopathic"

    # Robust classifier resists acute infection confounder through multimodal imaging signs
    robust_res = adversarial_arena_engine.evaluate_model("mock_robust", p_case)
    assert robust_res.is_top1_correct is True
    assert robust_res.predicted_disease_id == "wilson_disease"


# -----------------------------------------------------------------------------
# 6. Full Experiment Execution & Correct Metric Calculations
# -----------------------------------------------------------------------------
def test_arena_experiment_execution_and_metrics():
    cfg = ArenaExperimentConfig(
        disease_selection="all",
        num_cases_per_disease=2,  # 2 * 3 = 6 cases
        random_seed=42,
        model_type="reference_baseline",
        search_strategy="sweep",
        noise_sigma=0.10,
        missing_lab_rate=0.20,
        inject_confounding_infection=False
    )

    result = adversarial_arena_engine.run_experiment(cfg)

    assert result.status == "COMPLETED"
    assert len(result.cases) == 6
    assert result.metrics.total_cases_attempted == 6
    assert result.metrics.valid_cases_count >= 5

    # Check mathematically sound metrics
    if result.metrics.valid_cases_count > 0:
        assert 0.0 <= result.metrics.baseline_accuracy <= 1.0
        assert 0.0 <= result.metrics.perturbed_accuracy <= 1.0
        assert result.metrics.accuracy_degradation == round(
            result.metrics.baseline_accuracy - result.metrics.perturbed_accuracy, 4
        )
        assert 0.0 <= result.metrics.prediction_instability_rate <= 1.0
        assert 0.0 <= result.metrics.failure_rate <= 1.0

    # Verify disease breakdown structure
    for d in ["wilson_disease", "fabry_disease", "gaucher_disease"]:
        assert d in result.metrics.by_disease
        assert result.metrics.by_disease[d]["total_cases"] == 2

    # Verify perturbation category tracking
    assert len(result.metrics.by_perturbation_type) > 0


# -----------------------------------------------------------------------------
# 7. Failure Discovery & Instability Classification
# -----------------------------------------------------------------------------
def test_failure_classification_categories():
    cfg = ArenaExperimentConfig(
        disease_selection="wilson_disease",
        num_cases_per_disease=3,
        random_seed=999,
        model_type="mock_fragile",  # Sensitive to infection
        search_strategy="sweep",
        noise_sigma=0.15,
        missing_lab_rate=0.20,
        inject_confounding_infection=True
    )

    result = adversarial_arena_engine.run_experiment(cfg)

    # With confounding infection, mock_fragile should produce failure cases
    failures = [c for c in result.cases if c.is_failure]
    assert len(failures) > 0

    valid_cats = {
        "NONE", "INCORRECT_PREDICTION", "PREDICTION_INSTABILITY",
        "CONFIDENCE_COLLAPSE", "CONSTRAINT_VIOLATION", "UNEVALUABLE"
    }
    for c in result.cases:
        assert c.failure_category in valid_cats
        if c.failure_category in ["INCORRECT_PREDICTION", "PREDICTION_INSTABILITY", "CONFIDENCE_COLLAPSE", "CONSTRAINT_VIOLATION"]:
            assert c.is_failure is True


# -----------------------------------------------------------------------------
# 8. External Model Mocking: Timeout and Error Handling
# -----------------------------------------------------------------------------
def test_external_model_mock_timeout(test_client):
    patient = patient_generator.generate_patient(disease_id="fabry_disease", seed=321)
    tc = perturbation_engine.create_arena_case(
        patient, PerturbationConfig(reproducibility_seed=321)
    )["exportable_test_case"]

    with patch("requests.post", side_effect=requests.exceptions.Timeout("Timed out")):
        res = adversarial_arena_engine.evaluate_model(
            model_type="external_http",
            test_case=tc,
            external_url="http://mock-diagnostic-server.internal/predict"
        )
        assert res.predicted_disease_id == "TIMEOUT"
        assert res.is_top1_correct is False
        assert "timed out" in res.error_message.lower()


def test_external_model_mock_error_status(test_client):
    patient = patient_generator.generate_patient(disease_id="gaucher_disease", seed=654)
    tc = perturbation_engine.create_arena_case(
        patient, PerturbationConfig(reproducibility_seed=654)
    )["exportable_test_case"]

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = "Service Unavailable"

    with patch("requests.post", return_value=mock_resp):
        res = adversarial_arena_engine.evaluate_model(
            model_type="external_http",
            test_case=tc,
            external_url="http://mock-diagnostic-server.internal/predict"
        )
        assert res.predicted_disease_id == "EXTERNAL_ERROR"
        assert res.is_top1_correct is False
        assert "503" in res.error_message


# -----------------------------------------------------------------------------
# 9. Experiment Reproducibility with Saved Seed
# -----------------------------------------------------------------------------
def test_experiment_reproducibility():
    cfg1 = ArenaExperimentConfig(
        disease_selection="gaucher_disease",
        num_cases_per_disease=2,
        random_seed=7711,
        model_type="reference_baseline",
        search_strategy="sweep",
        noise_sigma=0.1,
        missing_lab_rate=0.2
    )
    cfg2 = ArenaExperimentConfig(
        disease_selection="gaucher_disease",
        num_cases_per_disease=2,
        random_seed=7711,
        model_type="reference_baseline",
        search_strategy="sweep",
        noise_sigma=0.1,
        missing_lab_rate=0.2
    )

    r1 = adversarial_arena_engine.run_experiment(cfg1)
    r2 = adversarial_arena_engine.run_experiment(cfg2)

    assert len(r1.cases) == len(r2.cases)
    for c1, c2 in zip(r1.cases, r2.cases):
        assert c1.seed == c2.seed
        assert c1.baseline_prediction.predicted_disease_id == c2.baseline_prediction.predicted_disease_id
        assert c1.perturbed_prediction.predicted_disease_id == c2.perturbed_prediction.predicted_disease_id
        assert c1.failure_category == c2.failure_category


# -----------------------------------------------------------------------------
# 10. Export Correctness (JSON & CSV)
# -----------------------------------------------------------------------------
def test_experiment_export_json_and_csv():
    cfg = ArenaExperimentConfig(
        disease_selection="fabry_disease",
        num_cases_per_disease=2,
        random_seed=4321
    )
    exp = adversarial_arena_engine.run_experiment(cfg)

    # Test JSON export
    json_str = adversarial_arena_engine.export_experiment_json(exp.experiment_id)
    data = json.loads(json_str)
    assert data["experiment_id"] == exp.experiment_id
    assert "metrics" in data
    assert len(data["cases"]) == 2

    # Test CSV export
    csv_str = adversarial_arena_engine.export_experiment_csv(exp.experiment_id)
    lines = csv_str.strip().split("\n")
    assert len(lines) == 3  # Header + 2 rows
    headers = lines[0].split(",")
    assert "experiment_id" in headers
    assert "failure_category" in headers
    assert "is_failure" in headers
    assert "diff_summary" in headers


# -----------------------------------------------------------------------------
# 11. REST API Endpoints Integration
# -----------------------------------------------------------------------------
def test_arena_api_endpoints(test_client):
    # 1. Capabilities
    r_cap = test_client.get("/api/diagnostic-arena/capabilities")
    assert r_cap.status_code == 200
    caps = r_cap.json()
    assert len(caps["supported_diseases"]) == 3
    assert len(caps["supported_models"]) >= 4

    # 2. Run Experiment via API
    payload = {
        "disease_selection": "wilson_disease",
        "num_cases_per_disease": 2,
        "random_seed": 5432,
        "model_type": "reference_baseline",
        "search_strategy": "sweep",
        "noise_sigma": 0.1,
        "missing_lab_rate": 0.2,
        "atypical_age_shift_years": 0,
        "inject_confounding_infection": False
    }
    r_run = test_client.post("/api/diagnostic-arena/experiments/run", json=payload)
    assert r_run.status_code == 200
    exp_data = r_run.json()
    exp_id = exp_data["experiment_id"]
    assert exp_data["status"] == "COMPLETED"
    assert len(exp_data["cases"]) == 2

    # 3. Retrieve Experiment
    r_get = test_client.get(f"/api/diagnostic-arena/experiments/{exp_id}")
    assert r_get.status_code == 200
    assert r_get.json()["experiment_id"] == exp_id

    # 4. List Experiments History
    r_list = test_client.get("/api/diagnostic-arena/experiments")
    assert r_list.status_code == 200
    assert any(e["experiment_id"] == exp_id for e in r_list.json())

    # 5. Inspect Single Case
    case_id = exp_data["cases"][0]["case_id"]
    r_case = test_client.get(f"/api/diagnostic-arena/cases/{case_id}")
    assert r_case.status_code == 200
    c_data = r_case.json()
    assert c_data["case_id"] == case_id
    assert "applied_transformations" in c_data
    assert "diff_summary" in c_data

    # 6. Export JSON & CSV via API
    r_exp_json = test_client.get(f"/api/diagnostic-arena/experiments/{exp_id}/export?format=json")
    assert r_exp_json.status_code == 200
    assert "application/json" in r_exp_json.headers["content-type"]

    r_exp_csv = test_client.get(f"/api/diagnostic-arena/experiments/{exp_id}/export?format=csv")
    assert r_exp_csv.status_code == 200
    assert "text/csv" in r_exp_csv.headers["content-type"]

    # 7. 404 on nonexistent experiment
    r_404 = test_client.get("/api/diagnostic-arena/experiments/NONEXISTENT_EXP")
    assert r_404.status_code == 404
