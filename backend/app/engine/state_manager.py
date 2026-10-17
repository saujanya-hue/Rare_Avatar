"""Longitudinal Patient State Engine and Session Storage."""
import copy
from typing import Dict, Optional, List, Any
from app.schemas.patient import (
    SyntheticPatientSpecification, TraineeSafePatientView,
    LabMeasurement, ImagingStudy, ClinicalEncounterNote
)
from app.disease_models import disease_registry
import numpy as np


class PatientStateManager:
    def __init__(self):
        self._patients: Dict[str, SyntheticPatientSpecification] = {}

    def register_patient(self, patient: SyntheticPatientSpecification) -> None:
        self._patients[patient.patient_id] = patient

    def get_patient(self, patient_id: str) -> Optional[SyntheticPatientSpecification]:
        if not patient_id:
            return next(iter(self._patients.values())) if self._patients else None
        if patient_id in self._patients:
            return self._patients[patient_id]
        # Graceful prefix/disease fallback if stale session ID is received
        for pid, pt in self._patients.items():
            if pid.startswith(patient_id[:9]) or pt.disease.disease_id in patient_id.lower():
                return pt
        if self._patients:
            return next(iter(self._patients.values()))
        return None

    def list_patients(self) -> List[SyntheticPatientSpecification]:
        return list(self._patients.values())

    def get_trainee_view(self, patient_id: str) -> Optional[TraineeSafePatientView]:
        patient = self.get_patient(patient_id)
        if not patient:
            return None

        # Filter only revealed symptoms
        revealed_symptoms = [s for s in patient.symptoms if s.is_revealed]

        # Filter only ordered labs
        available_labs = [lab for lab in patient.lab_history if lab.ordered and lab.reported]

        # Filter only ordered imaging
        available_imaging = [img for img in patient.imaging_studies if img.ordered and img.reported]

        # Available encounter notes
        available_notes = [note for note in patient.clinical_notes if note.timestamp_month <= patient.current_simulation_month]

        # Build test catalog of tests that CAN be ordered
        catalog = []
        for lab in patient.lab_history:
            if not lab.ordered:
                catalog.append({"type": "lab", "code": lab.test_code, "name": lab.test_name, "category": lab.category})
        for img in patient.imaging_studies:
            if not img.ordered:
                catalog.append({"type": "imaging", "code": img.study_id, "name": img.modality, "category": img.anatomical_region})

        return TraineeSafePatientView(
            patient_id=patient.patient_id,
            age_years=patient.demographics.age_years,
            biological_sex=patient.demographics.biological_sex,
            ethnicity=patient.demographics.ethnicity,
            current_simulation_month=patient.current_simulation_month,
            chief_complaint=patient.clinical_notes[0].chief_complaint if patient.clinical_notes else "Initial clinical encounter",
            active_symptoms_revealed=revealed_symptoms,
            available_labs=available_labs,
            available_imaging=available_imaging,
            available_notes=available_notes,
            active_treatment=patient.active_treatment,
            available_test_catalog=catalog,
            simulation_status=f"Month {patient.current_simulation_month} - {patient.baseline_disease_stage}"
        )

    def order_investigation(self, patient_id: str, inv_type: str, test_code_or_study_id: str) -> Dict[str, Any]:
        patient = self.get_patient(patient_id)
        if not patient:
            return {"success": False, "message": f"Patient {patient_id} not found."}

        if inv_type == "lab":
            for lab in patient.lab_history:
                if lab.test_code == test_code_or_study_id:
                    lab.ordered = True
                    lab.reported = True
                    return {
                        "success": True,
                        "type": "lab",
                        "message": f"Laboratory test '{lab.test_name}' completed and reported.",
                        "result": lab.model_dump()
                    }
            return {"success": False, "message": f"Lab test with code '{test_code_or_study_id}' is not in the test panel."}

        elif inv_type == "imaging":
            for img in patient.imaging_studies:
                if img.study_id == test_code_or_study_id:
                    img.ordered = True
                    img.reported = True
                    return {
                        "success": True,
                        "type": "imaging",
                        "message": f"Imaging study '{img.modality}' performed and finalized by radiology.",
                        "result": img.model_dump()
                    }
            return {"success": False, "message": f"Imaging study '{test_code_or_study_id}' not found."}

        return {"success": False, "message": f"Unknown investigation type: {inv_type}"}

    def advance_time(self, patient_id: str, delta_months: int = 3) -> Dict[str, Any]:
        patient = self.get_patient(patient_id)
        if not patient:
            return {"success": False, "message": f"Patient {patient_id} not found."}

        patient.current_simulation_month += delta_months

        # Generate progressive notes & reveal previously hidden symptoms if onset reached
        for sym in patient.symptoms:
            if not sym.is_revealed and sym.onset_month <= patient.current_simulation_month:
                sym.is_revealed = True

        # If on treatment, update clinical status
        treatment_note = ""
        if patient.active_treatment:
            treatment_note = f" (Ongoing active treatment: {patient.active_treatment})"

        follow_up_note = ClinicalEncounterNote(
            encounter_id=f"enc_fu_m{patient.current_simulation_month}",
            timestamp_month=patient.current_simulation_month,
            encounter_type=f"Longitudinal Follow-up (+{delta_months} months)",
            chief_complaint=f"Follow-up visit at simulated Month {patient.current_simulation_month}{treatment_note}.",
            hpi=f"Patient reassessed after {delta_months} months. Clinical condition evaluated for disease trajectory changes.",
            physical_exam={"Status": f"Re-evaluated at Month {patient.current_simulation_month}."},
            assessment_and_plan=f"Longitudinal progression monitoring. Month {patient.current_simulation_month}.",
            disease_stage=patient.baseline_disease_stage
        )
        patient.clinical_notes.append(follow_up_note)

        return {
            "success": True,
            "patient_id": patient_id,
            "current_month": patient.current_simulation_month,
            "message": f"Simulation advanced by {delta_months} months to Month {patient.current_simulation_month}."
        }

    def apply_treatment(self, patient_id: str, scenario_id: str) -> Dict[str, Any]:
        patient = self.get_patient(patient_id)
        if not patient:
            return {"success": False, "message": f"Patient {patient_id} not found."}

        matched_scenario = None
        for scen in patient.treatment_scenarios:
            if scen.scenario_id == scenario_id:
                scen.is_active = True
                matched_scenario = scen
            else:
                scen.is_active = False

        if not matched_scenario:
            return {"success": False, "message": f"Scenario '{scenario_id}' not found."}

        patient.active_treatment = matched_scenario.name
        return {
            "success": True,
            "patient_id": patient_id,
            "active_treatment": matched_scenario.name,
            "description": matched_scenario.description,
            "trajectory_points": len(matched_scenario.trajectory)
        }


state_manager = PatientStateManager()
