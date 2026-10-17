import pytest
from app.generators.patient_generator import patient_generator
from app.validation.privacy_auditor import privacy_auditor


def test_privacy_auditor_clean_synthetic_patient():
    patient = patient_generator.generate_patient(disease_id="gaucher_disease", seed=555)
    results, max_ngram, min_dist = privacy_auditor.audit_privacy(patient)

    assert len(results) == 2
    # Verify synthetic patient does not copy verbatim literature snippets
    assert max_ngram < 0.20
    assert all(r.passed for r in results)
