import pytest
from app.generators.patient_generator import patient_generator
from app.engine.dialogue_manager import dialogue_manager


def test_dialogue_manager_symptom_inquiry():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    resp = dialogue_manager.process_inquiry(patient, "Are you experiencing any tremor in your hands?")

    assert resp.intent_detected == "SYMPTOM_EXPLORATION"
    assert "tremor" in resp.avatar_response.lower()
    assert len(resp.evidence_citations) > 0


def test_dialogue_manager_family_history():
    patient = patient_generator.generate_patient(disease_id="fabry_disease", seed=42)
    resp = dialogue_manager.process_inquiry(patient, "Does anyone in your family have kidney or heart disease?")

    assert resp.intent_detected == "FAMILY_HISTORY_INQUIRY"
    assert "dialysis" in resp.avatar_response.lower() or "kidney" in resp.avatar_response.lower()


def test_dialogue_manager_order_direction():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    resp = dialogue_manager.process_inquiry(patient, "Can you order a ceruloplasmin test right now?")

    assert resp.intent_detected == "INVESTIGATION_ORDER_INTENT"
    assert "order" in resp.avatar_response.lower()


def test_dialogue_manager_duration_inquiry():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    resp = dialogue_manager.process_inquiry(patient, "How many days are you having this problem?")

    assert resp.intent_detected == "ONSET_AND_DURATION_INQUIRY"
    assert "months" in resp.avatar_response.lower() or "days" in resp.avatar_response.lower()
    assert len(resp.revealed_findings) > 0


def test_dialogue_manager_progression_inquiry():
    patient = patient_generator.generate_patient(disease_id="wilson_disease", seed=42)
    resp = dialogue_manager.process_inquiry(patient, "Is this condition getting worse over time?")

    assert resp.intent_detected == "PROGRESSION_AND_SEVERITY_INQUIRY"
    assert "worse" in resp.avatar_response.lower()

