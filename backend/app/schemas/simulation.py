from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class DialogueInquiryRequest(BaseModel):
    patient_id: str
    query_text: str
    inquiry_category: Optional[str] = "symptom_inquiry"  # "symptom_inquiry", "history_request", "test_order", "intervention_command", "general"


class DialogueResponse(BaseModel):
    patient_id: str
    query_text: str
    avatar_response: str
    intent_detected: str
    clinical_entities_identified: List[str]
    revealed_findings: List[str]
    uncertainty_statement: Optional[str] = None
    evidence_citations: List[str] = []
    simulation_month: int


class AdvanceSimulationRequest(BaseModel):
    patient_id: str
    advance_months: int = 3


class OrderInvestigationRequest(BaseModel):
    patient_id: str
    investigation_type: str  # "lab" or "imaging"
    test_code_or_study_id: str


class ApplyInterventionRequest(BaseModel):
    patient_id: str
    scenario_id: str  # e.g., "penicillamine_chelation", "delay_3_months", "untreated"


# ============================================================================
# CLINICAL WHAT-IF LAB BRANCHING SCHEMAS
# ============================================================================

class WhatIfBranchConfig(BaseModel):
    patient_id: str
    branch_name: str
    intervention_type: str = "Targeted Therapy"  # "Targeted Therapy", "Delayed Treatment", "Discontinuation / Non-Adherence", "Alternative Agent", "Untreated Natural History"
    intervention_agent: str = "First-Line Therapy"  # e.g., "D-Penicillamine", "Agalsidase Beta", "Imiglucerase", "Untreated"
    origin_month: int = 0
    notes: Optional[str] = None


class WhatIfTrajectoryPoint(BaseModel):
    month: int
    primary_biomarker_name: str
    primary_biomarker_value: float
    unit: str
    clinical_status: str
    symptom_severity_mean: float
    active_symptoms_count: int
    ci_low: float
    ci_high: float


class WhatIfBranchState(BaseModel):
    branch_id: str
    parent_branch_id: Optional[str] = None
    patient_id: str
    branch_name: str
    disease_id: str
    disease_name: str
    intervention_type: str
    intervention_agent: str
    origin_month: int
    current_month: int
    is_active: bool = True
    trajectory: List[WhatIfTrajectoryPoint] = []
    created_at: str


class WhatIfAdvanceBranchRequest(BaseModel):
    branch_id: str
    advance_months: int = 6


class WhatIfComparisonRequest(BaseModel):
    patient_id: str
    branch_ids: List[str]


class WhatIfComparisonReport(BaseModel):
    comparison_id: str
    patient_id: str
    disease_id: str
    disease_name: str
    branches: Dict[str, WhatIfBranchState] = {}
    timeline_months: List[int] = []
    comparative_metrics: List[Dict[str, Any]] = []
    clinical_recommendation: str = ""
    created_at: str = ""
