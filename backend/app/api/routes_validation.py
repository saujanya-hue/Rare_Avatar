"""REST API routes for Clinical Consistency and Privacy Audit Reports."""
from fastapi import APIRouter, HTTPException
import datetime
from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.validation import ComprehensiveValidationReport
from app.engine.state_manager import state_manager
from app.validation.consistency_checker import consistency_checker
from app.validation.privacy_auditor import privacy_auditor

router = APIRouter(prefix="/api/validation", tags=["Clinical Consistency & Privacy Validation"])


def _build_validation_report(patient: SyntheticPatientSpecification) -> ComprehensiveValidationReport:
    # 1. Clinical Consistency Guardian Checks (5 categories)
    clinical_results = consistency_checker.validate_patient(patient)

    # 2. Privacy & Anti-Memorization Audit
    privacy_results, max_ngram, min_dist = privacy_auditor.audit_privacy(patient)

    # Calculate overall metrics
    total_checks = len(clinical_results) + len(privacy_results)
    failed_checks = sum(1 for r in clinical_results if not r.passed) + sum(1 for r in privacy_results if not r.passed)
    passed_checks = total_checks - failed_checks

    status = "AUTOMATED_CHECKS_PASSED" if failed_checks == 0 else "VIOLATIONS_DETECTED"
    privacy_risk = "LOW (Safe Synthetic)" if min_dist >= 0.15 and max_ngram < 0.20 else "MODERATE_OR_HIGH"

    category_summary = consistency_checker.compute_category_summary(clinical_results)
    guardian_verdict = consistency_checker.determine_guardian_verdict(clinical_results)

    return ComprehensiveValidationReport(
        patient_id=patient.patient_id,
        overall_status=status,
        guardian_verdict=guardian_verdict,
        category_summary=category_summary,
        expert_review_status="PENDING_FORMAL_EXPERT_REVIEW",
        total_checks=total_checks,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        clinical_consistency_results=clinical_results,
        privacy_audit_results=privacy_results,
        overall_privacy_risk=privacy_risk,
        max_literature_ngram_overlap=max_ngram,
        nearest_reference_patient_distance=min_dist,
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


@router.get("/audit/{patient_id}", response_model=ComprehensiveValidationReport)
def run_comprehensive_audit(patient_id: str):
    """Execute full 5-category Clinical Consistency Guardian check & privacy audit on an active patient."""
    patient = state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    return _build_validation_report(patient)


@router.post("/validate-case", response_model=ComprehensiveValidationReport)
def validate_synthetic_case(patient: SyntheticPatientSpecification):
    """
    Validate an uploaded or custom synthetic patient specification against
    all 5 categories of the Clinical Consistency Guardian.
    """
    try:
        return _build_validation_report(patient)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
