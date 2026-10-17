"""REST API routes for Interactive Avatar Consultation and Longitudinal Simulation."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.schemas.simulation import (
    DialogueInquiryRequest, DialogueResponse, AdvanceSimulationRequest,
    OrderInvestigationRequest, ApplyInterventionRequest
)
from app.engine.state_manager import state_manager
from app.engine.dialogue_manager import dialogue_manager

router = APIRouter(prefix="/api/simulation", tags=["Simulation & Avatar Dialogue"])


@router.post("/inquiry", response_model=DialogueResponse)
def clinical_inquiry(req: DialogueInquiryRequest):
    patient = state_manager.get_patient(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {req.patient_id} not found.")

    response = dialogue_manager.process_inquiry(patient, req.query_text)
    return response


@router.post("/order-investigation")
def order_investigation(req: OrderInvestigationRequest):
    res = state_manager.order_investigation(
        patient_id=req.patient_id,
        inv_type=req.investigation_type,
        test_code_or_study_id=req.test_code_or_study_id
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/advance-time")
def advance_simulation_time(req: AdvanceSimulationRequest):
    res = state_manager.advance_time(req.patient_id, req.advance_months)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/apply-treatment")
def apply_treatment_scenario(req: ApplyInterventionRequest):
    res = state_manager.apply_treatment(req.patient_id, req.scenario_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res
