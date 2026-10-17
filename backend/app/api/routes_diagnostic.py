"""REST API routes for Diagnostic Algorithm Stress-Testing and Benchmarking."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.schemas.diagnostic import (
    PerturbationConfig, ExportableTestCase, AlgorithmSubmission, StressTestEvaluationResult
)
from app.engine.state_manager import state_manager
from app.stress_testing.perturbation_engine import perturbation_engine
from app.stress_testing.benchmark_runner import benchmark_runner

router = APIRouter(prefix="/api/diagnostic-eval", tags=["Diagnostic Algorithm Stress-Testing"])


@router.post("/create-test-case", response_model=ExportableTestCase)
def create_perturbed_test_case(
    patient_id: str = Query(...),
    noise_sigma: float = Query(0.1, ge=0.0, le=0.5),
    missing_lab_rate: float = Query(0.2, ge=0.0, le=0.8),
    atypical_age_shift_years: int = Query(0, ge=-20, le=20),
    inject_confounding_infection: bool = Query(False),
    seed: int = Query(42)
):
    patient = state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    cfg = PerturbationConfig(
        noise_sigma=noise_sigma,
        missing_lab_rate=missing_lab_rate,
        atypical_age_shift_years=atypical_age_shift_years,
        inject_confounding_infection=inject_confounding_infection,
        reproducibility_seed=seed
    )

    tc = perturbation_engine.create_perturbed_test_case(patient, cfg)
    benchmark_runner.store_test_case(tc)
    return tc


@router.post("/evaluate-baseline", response_model=StressTestEvaluationResult)
def evaluate_baseline_classifier(test_case_id: str = Query(...)):
    tc = benchmark_runner.get_test_case(test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail=f"Test case {test_case_id} not found.")

    # Run reference classifier
    submission = benchmark_runner.ref_classifier.predict(tc)
    eval_result = benchmark_runner.evaluate_submission(submission)
    return eval_result


@router.post("/submit-external", response_model=StressTestEvaluationResult)
def submit_external_diagnostic_prediction(submission: AlgorithmSubmission):
    try:
        eval_result = benchmark_runner.evaluate_submission(submission)
        return eval_result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history", response_model=List[StressTestEvaluationResult])
def get_benchmark_history():
    return benchmark_runner.get_evaluation_history()
