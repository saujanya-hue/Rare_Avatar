import pytest
from app.generators.patient_generator import patient_generator
from app.schemas.diagnostic import PerturbationConfig
from app.stress_testing.perturbation_engine import perturbation_engine
from app.stress_testing.benchmark_runner import benchmark_runner


def test_perturbation_engine_applies_noise_and_dropout():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    cfg = PerturbationConfig(
        noise_sigma=0.2,
        missing_lab_rate=0.5,
        atypical_age_shift_years=5,
        inject_confounding_infection=True,
        reproducibility_seed=123
    )
    tc = perturbation_engine.create_perturbed_test_case(patient, cfg)

    assert tc.test_case_id.startswith("TC-STRESS-")
    # Verify input demographics has shifted age
    assert tc.input_demographics["age_years"] == patient.demographics.age_years + 5
    # Verify confounding infection injected
    assert any(l["test_code"] == "CRP" for l in tc.input_laboratory)
    # Ground truth is preserved
    assert tc.ground_truth_disease_id == "wilson_disease"


def test_benchmark_runner_evaluation():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    cfg = PerturbationConfig(noise_sigma=0.05, missing_lab_rate=0.0, reproducibility_seed=42)
    tc = perturbation_engine.create_perturbed_test_case(patient, cfg)

    benchmark_runner.store_test_case(tc)
    submission = benchmark_runner.ref_classifier.predict(tc)
    result = benchmark_runner.evaluate_submission(submission)

    assert result.is_top1_correct is True
    assert result.robustness_score > 0.5
