"""REST API routes for Synthetic Patient Generation and Retrieval."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from app.schemas.patient import SyntheticPatientSpecification, TraineeSafePatientView
from app.generators.patient_generator import patient_generator
from app.engine.state_manager import state_manager
from app.disease_models import disease_registry

router = APIRouter(prefix="/api/patients", tags=["Synthetic Patients"])


@router.post("/generate", response_model=SyntheticPatientSpecification)
def generate_patient(
    disease_id: str = Query(..., description="Disease identifier (e.g. wilson_disease, fabry_disease, gaucher_disease)"),
    age_years: Optional[int] = Query(None, description="Optional patient age in years"),
    biological_sex: Optional[str] = Query(None, description="Optional biological sex (Male/Female)"),
    phenotype: Optional[str] = Query(None, description="Optional specific disease phenotype"),
    seed: Optional[int] = Query(None, description="Optional reproducibility seed")
):
    try:
        patient = patient_generator.generate_patient(
            disease_id=disease_id,
            age_years=age_years,
            biological_sex=biological_sex,
            phenotype=phenotype,
            seed=seed
        )
        state_manager.register_patient(patient)
        return patient
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[Dict[str, Any]])
def list_patients():
    patients = state_manager.list_patients()
    return [
        {
            "patient_id": p.patient_id,
            "disease_id": p.disease.disease_id,
            "disease_name": p.disease.disease_name,
            "age_years": p.demographics.age_years,
            "biological_sex": p.demographics.biological_sex,
            "ethnicity": p.demographics.ethnicity,
            "stage": p.baseline_disease_stage,
            "current_month": p.current_simulation_month,
            "created_at_utc": p.created_at_utc
        }
        for p in patients
    ]


@router.get("/{patient_id}", response_model=SyntheticPatientSpecification)
def get_patient_full_spec(patient_id: str):
    p = state_manager.get_patient(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")
    return p


@router.get("/{patient_id}/trainee-view", response_model=TraineeSafePatientView)
def get_patient_trainee_view(patient_id: str):
    view = state_manager.get_trainee_view(patient_id)
    if not view:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")
    return view
