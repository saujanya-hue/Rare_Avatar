"""Schemas for Clinical Mystery Mode."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.schemas.patient import ClinicalSymptom, LabMeasurement, ImagingStudy, EvidenceReference


class MysterySessionConfig(BaseModel):
    difficulty: str = "intermediate"  # "beginner", "intermediate", "advanced"
    disease_selection: str = "random"  # "wilson_disease", "fabry_disease", "gaucher_disease", "random"
    trainee_id: str = "TR-8041"
    random_seed: Optional[int] = None


class MysteryInvestigationItem(BaseModel):
    investigation_id: str
    modality: str  # "LABORATORY", "IMAGING"
    code_or_acronym: str
    name: str
    simulated_cost_usd: float
    turnaround_hours: float
    result_summary: str
    is_abnormal: bool
    timestamp_ordered: str


class MysteryCaseView(BaseModel):
    session_id: str
    trainee_id: str
    difficulty: str
    patient_id: str
    age_years: int
    biological_sex: str
    ethnicity: str
    chief_complaint: str
    available_symptoms: List[ClinicalSymptom] = Field(default_factory=list)
    ordered_investigations: List[MysteryInvestigationItem] = Field(default_factory=list)
    accumulated_cost_usd: float = 0.0
    accumulated_turnaround_hours: float = 0.0
    status: str = "IN_PROGRESS"  # "IN_PROGRESS", "SUBMITTED"
    started_at: str


class MysteryInvestigationOrderRequest(BaseModel):
    session_id: str
    investigation_type: str  # "lab" or "imaging"
    code_or_acronym: str


class MysteryInquiryRequest(BaseModel):
    session_id: str
    query_text: str


class MysterySubmissionRequest(BaseModel):
    session_id: str
    predicted_disease_id: str
    predicted_disease_name: str
    confidence_score: float  # 0.0 to 1.0
    differential_diagnoses: List[Dict[str, float]] = Field(default_factory=list)
    clinical_justification: str
    management_plan: Optional[str] = None


class MysteryScorecard(BaseModel):
    is_top1_correct: bool
    is_top3_correct: bool
    accuracy_score: float  # 0 to 100
    cost_efficiency_score: float  # 0 to 100
    diagnostic_parsimony_score: float  # 0 to 100
    overall_clinical_score: float  # 0 to 100
    performance_band: str  # "EXEMPLARY (HONORS)", "PROFICIENT", "MARGINAL", "NEEDS_REMEDIATION"


class EducationalDebriefing(BaseModel):
    correct_disease_name: str
    omim_id: str
    phenotype_summary: str
    pathognomonic_findings: List[str]
    common_pitfalls_avoided_or_committed: List[str]
    relevant_guidelines: List[EvidenceReference] = Field(default_factory=list)
    clinical_takeaway: str


class MysteryDebriefingReport(BaseModel):
    session_id: str
    trainee_id: str
    difficulty: str
    ground_truth_disease_id: str
    ground_truth_disease_name: str
    submission: MysterySubmissionRequest
    scorecard: MysteryScorecard
    total_cost_usd: float
    total_turnaround_hours: float
    investigations_count: int
    inquiries_count: int
    debriefing: EducationalDebriefing
    completed_at: str
