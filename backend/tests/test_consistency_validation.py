import pytest
from app.generators.patient_generator import patient_generator
from app.validation.consistency_checker import consistency_checker


def test_consistency_checker_on_valid_patient():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    results = consistency_checker.validate_patient(patient)

    fatal_errors = [r for r in results if not r.passed and r.severity == "FATAL_ERROR"]
    assert len(fatal_errors) == 0, f"Unexpected fatal errors: {[r.details for r in fatal_errors]}"


def test_consistency_checker_catches_physiological_violation():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    # Deliberately violate ceruloplasmin constraint
    for lab in patient.lab_history:
        if lab.test_code == "CERULOPLASMIN":
            lab.value = 45.0  # Impossible normal/high in symptomatic classical Wilson disease

    results = consistency_checker.validate_patient(patient)
    failed = [r for r in results if not r.passed and r.rule_id == "WD_RULE_CERULOPLASMIN_UPPER_BOUND"]
    assert len(failed) == 1
    assert failed[0].severity == "FATAL_ERROR"
