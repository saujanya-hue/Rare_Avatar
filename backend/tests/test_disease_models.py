import pytest
import numpy as np
from app.disease_models import disease_registry
from app.knowledge.evidence_base import evidence_base


def test_disease_registry_contains_supported_diseases():
    diseases = [d["disease_id"] for d in disease_registry.list_available_diseases()]
    assert "wilson_disease" in diseases
    assert "fabry_disease" in diseases
    assert "gaucher_disease" in diseases


def test_wilson_disease_model_output():
    model = disease_registry.get_model("wilson_disease")
    assert model is not None
    rng = np.random.default_rng(42)

    symptoms = model.generate_symptoms(24, "Active", "Mixed Hepato-Neurological", rng)
    assert len(symptoms) >= 3
    assert any(s.category == "Neurologic" for s in symptoms)

    labs = model.generate_laboratory_trajectories(0, "Active", "Mixed Hepato-Neurological", rng)
    lab_codes = [l.test_code for l in labs]
    assert "CERULOPLASMIN" in lab_codes
    assert "URINARY_COPPER_24H" in lab_codes
    assert "AST" in lab_codes

    # Check ceruloplasmin is pathological
    cp = next(l for l in labs if l.test_code == "CERULOPLASMIN")
    assert cp.value < 20.0
    assert cp.uncertainty.epistemic_confidence_score > 0.5

    imaging = model.generate_imaging_studies(0, "Active", "Mixed Hepato-Neurological", rng)
    assert len(imaging) >= 2
    assert any("Face of Giant Panda" in sign for study in imaging for sign in study.pathological_signs)

    scenarios = model.generate_treatment_scenarios(0, "Active", "Mixed Hepato-Neurological")
    assert len(scenarios) >= 2


def test_fabry_disease_model_output():
    model = disease_registry.get_model("fabry_disease")
    assert model is not None
    rng = np.random.default_rng(42)

    symptoms = model.generate_symptoms(30, "Active", "Classic Early-Onset", rng)
    assert any("Acroparesthesias" in s.name for s in symptoms)

    labs = model.generate_laboratory_trajectories(0, "Active", "Classic Early-Onset", rng)
    lyso = next(l for l in labs if l.test_code == "LYSO_GB3")
    assert lyso.value > 0.8
    assert lyso.is_abnormal is True

    imaging = model.generate_imaging_studies(0, "Active", "Classic Early-Onset", rng)
    cmr = imaging[0]
    assert "T1 Mapping" in cmr.modality


def test_gaucher_disease_model_output():
    model = disease_registry.get_model("gaucher_disease")
    assert model is not None
    rng = np.random.default_rng(42)

    labs = model.generate_laboratory_trajectories(0, "Active", "Classic Non-Neuronopathic Type 1", rng)
    plt = next(l for l in labs if l.test_code == "PLATELETS")
    assert plt.value < 150.0  # Thrombocytopenia

    imaging = model.generate_imaging_studies(0, "Active", "Classic Non-Neuronopathic Type 1", rng)
    assert any("Erlenmeyer Flask Deformity" in s for img in imaging for s in img.pathological_signs)
