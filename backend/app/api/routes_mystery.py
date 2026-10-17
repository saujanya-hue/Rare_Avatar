"""REST API routes for Clinical Mystery Mode."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from app.schemas.mystery import (
    MysterySessionConfig, MysteryCaseView, MysteryInvestigationItem,
    MysteryInvestigationOrderRequest, MysteryInquiryRequest,
    MysterySubmissionRequest, MysteryDebriefingReport
)
from app.engine.mystery_manager import mystery_manager, INVESTIGATION_PRICE_CATALOG

router = APIRouter(prefix="/api/mystery", tags=["Clinical Mystery Mode"])


@router.post("/start", response_model=MysteryCaseView)
def start_mystery_session(config: MysterySessionConfig):
    """
    Initiate an interactive mystery clinical diagnostic challenge.
    Selects or generates a rare-disease avatar, strictly blindfolds trainee to ground truth,
    and initializes cost and turnaround time tracking based on chosen difficulty.
    """
    try:
        return mystery_manager.start_session(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start mystery session: {str(e)}")


@router.get("/session/{session_id}", response_model=MysteryCaseView)
def get_mystery_session(session_id: str):
    """Retrieve current blinded case view, active investigations, and accumulated expenditure."""
    view = mystery_manager.get_session_view(session_id)
    if not view:
        raise HTTPException(status_code=404, detail=f"Mystery session '{session_id}' not found.")
    return view


@router.post("/inquire")
def send_mystery_inquiry(req: MysteryInquiryRequest):
    """Conduct interactive clinical history-taking dialogue with the blinded mystery avatar."""
    try:
        return mystery_manager.process_inquiry(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inquiry failed: {str(e)}")


@router.post("/order", response_model=MysteryInvestigationItem)
def order_mystery_investigation(req: MysteryInvestigationOrderRequest):
    """
    Order diagnostic lab test or imaging study. Incurs simulated financial cost
    and turnaround delay, revealing result upon completion.
    """
    try:
        return mystery_manager.order_investigation(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order failed: {str(e)}")


@router.post("/submit", response_model=MysteryDebriefingReport)
def submit_mystery_diagnosis(submission: MysterySubmissionRequest):
    """
    Submit final diagnostic formulation and management plan. Unblinds ground truth,
    computes multi-factorial performance scorecard (accuracy, cost, parsimony),
    and delivers comprehensive educational debriefing.
    """
    try:
        return mystery_manager.submit_diagnosis(submission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis submission failed: {str(e)}")


@router.get("/supervisor/sessions", response_model=List[MysteryDebriefingReport])
def list_supervisor_mystery_sessions():
    """Supervisor view: inspect all completed trainee mystery challenges and scoring summaries."""
    return mystery_manager.list_supervisor_sessions()


@router.get("/catalog/pricing")
def get_investigation_pricing_catalog():
    """Retrieve simulated investigation financial costs and turnaround time schedules."""
    return INVESTIGATION_PRICE_CATALOG
