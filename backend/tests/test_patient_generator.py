import pytest
from app.generators.patient_generator import patient_generator


def test_patient_generation_reproducibility():
    pt1 = patient_generator.generate_patient(disease_id="wilson_disease", seed=12345)
    pt2 = patient_generator.generate_patient(disease_id="wilson_disease", seed=12345)

    assert pt1.demographics.age_years == pt2.demographics.age_years
    assert pt1.demographics.biological_sex == pt2.demographics.biological_sex
    assert len(pt1.symptoms) == len(pt2.symptoms)
    assert pt1.lab_history[0].value == pt2.lab_history[0].value


def test_patient_generation_evidence_attribution():
    pt = patient_generator.generate_patient(disease_id="fabry_disease", seed=999)
    assert len(pt.evidence_catalog) > 0
    # Every symptom and lab with evidence_ids should have keys present in evidence_catalog
    for sym in pt.symptoms:
        for eid in sym.evidence_ids:
            assert eid in pt.evidence_catalog
