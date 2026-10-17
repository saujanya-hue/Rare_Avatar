from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class ClinicalCheckResult(BaseModel):
    rule_id: str
    rule_name: str
    category: str  # "PHYSIOLOGICAL", "CROSS_MODAL", "TEMPORAL", "TREATMENT_MODEL", "EVIDENCE_GROUNDING"
    passed: bool
    status: str = "PASSED"  # "PASSED", "WARNING", "FAILED", "REQUIRES_REVIEW", "NOT_EVALUABLE"
    severity: str = "INFO"  # "FATAL_ERROR", "WARNING", "INFO"
    details: str
    expected_constraint: str
    observed_value: str
    affected_patient_field: Optional[str] = None
    rule_source: Optional[str] = None
    suggested_action: Optional[str] = None


class PrivacyCheckResult(BaseModel):
    check_name: str
    metric: str
    threshold: float
    computed_score: float
    passed: bool
    details: str


class ComprehensiveValidationReport(BaseModel):
    patient_id: str
    overall_status: str  # "AUTOMATED_CHECKS_PASSED", "VIOLATIONS_DETECTED", "PENDING"
    guardian_verdict: str = "FULL_CLINICAL_CONCORDANCE"  # "FULL_CLINICAL_CONCORDANCE", "MINOR_DISCREPANCIES_DETECTED", "CRITICAL_PATHOPHYSIOLOGICAL_BREACH"
    category_summary: Dict[str, Dict[str, int]] = {}
    expert_review_status: str = "PENDING_FORMAL_EXPERT_REVIEW"  # Clearly labeled as pending expert review
    expert_validation_note: str = (
        "This case has been evaluated by automated deterministic physiological, cross-modal, temporal, treatment, and evidence consistency rules. "
        "Formal board-certified clinical expert sign-off has not yet been conducted and is required before formal institutional deployment."
    )
    total_checks: int
    passed_checks: int
    failed_checks: int
    clinical_consistency_results: List[ClinicalCheckResult]
    privacy_audit_results: List[PrivacyCheckResult]
    overall_privacy_risk: str  # "LOW (Safe Synthetic)", "MODERATE", "HIGH"
    max_literature_ngram_overlap: float
    nearest_reference_patient_distance: float
    timestamp_utc: str
