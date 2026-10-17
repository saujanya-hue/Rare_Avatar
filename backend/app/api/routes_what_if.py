"""REST API routes for Clinical What-If Lab Branching Simulation."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Response

from app.schemas.simulation import (
    WhatIfBranchConfig, WhatIfBranchState, WhatIfAdvanceBranchRequest,
    WhatIfComparisonRequest, WhatIfComparisonReport
)
from app.engine.what_if_engine import what_if_engine

router = APIRouter(prefix="/api/what-if", tags=["Clinical What-If Lab"])


@router.post("/branches/create", response_model=WhatIfBranchState)
def create_what_if_branch(config: WhatIfBranchConfig):
    """
    Fork an isolated simulation branch from an immutable snapshot of the active patient avatar.
    Allows independent counterfactual experimentation without mutating the baseline patient.
    """
    try:
        return what_if_engine.create_branch(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create branch: {str(e)}")


@router.get("/branches/patient/{patient_id}", response_model=List[WhatIfBranchState])
def list_patient_branches(patient_id: str):
    """List all simulation branches created for a specific patient avatar."""
    return what_if_engine.list_patient_branches(patient_id)


@router.get("/branches/{branch_id}", response_model=WhatIfBranchState)
def get_branch_details(branch_id: str):
    """Retrieve state, parameters, and full longitudinal trajectory for a specific branch."""
    st = what_if_engine.get_branch_state(branch_id)
    if not st:
        raise HTTPException(status_code=404, detail=f"Branch '{branch_id}' not found.")
    return st


@router.post("/branches/advance", response_model=WhatIfBranchState)
def advance_what_if_branch(req: WhatIfAdvanceBranchRequest):
    """
    Advance an isolated branch forward in simulation time by N months,
    computing trajectory dynamics and intervention response.
    """
    try:
        return what_if_engine.advance_branch(req.branch_id, advance_months=req.advance_months)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to advance branch: {str(e)}")


@router.post("/branches/compare", response_model=WhatIfComparisonReport)
def compare_what_if_branches(req: WhatIfComparisonRequest):
    """
    Compare multiple simulation branches side-by-side, analyzing biomarker deltas,
    symptom severity, and terminal clinical status with practice guideline recommendations.
    """
    try:
        return what_if_engine.compare_branches(req.patient_id, req.branch_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Branch comparison failed: {str(e)}")


@router.get("/branches/{branch_id}/export")
def export_branch_csv(branch_id: str):
    """Export longitudinal trajectory points and clinical statuses as CSV."""
    try:
        csv_data = what_if_engine.export_branch_csv(branch_id)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=what_if_{branch_id}.csv"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
