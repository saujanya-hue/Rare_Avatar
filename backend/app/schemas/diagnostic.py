from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class PerturbationConfig(BaseModel):
    noise_sigma: float = 0.1  # Gaussian measurement noise std relative to scale
    missing_lab_rate: float = 0.2  # Fraction of lab tests withheld
    atypical_age_shift_years: int = 0  # Shift age to atypical presentation window
    inject_confounding_infection: bool = False  # e.g., elevated CRP/WBC unrelated to rare disease
    variant_phenotype: Optional[str] = None  # e.g., "Isolated Hepatic", "Neuropsychiatric Predominant"
    reproducibility_seed: int = 42


class ExportableTestCase(BaseModel):
    test_case_id: str
    patient_id: str
    reproducibility_seed: int
    perturbation_applied: PerturbationConfig
    # Inputs provided to diagnostic algorithm (blinded to ground truth diagnosis)
    input_demographics: Dict[str, Any]
    input_symptoms: List[Dict[str, Any]]
    input_laboratory: List[Dict[str, Any]]
    input_imaging_summary: List[Dict[str, Any]]
    # Ground truth reference (held separately for scoring)
    ground_truth_disease_id: str
    ground_truth_disease_name: str
    ground_truth_omim: str
    ground_truth_stage: str


class AlgorithmSubmission(BaseModel):
    test_case_id: str
    predicted_disease_id: str
    predicted_disease_name: str
    confidence_score: float  # 0.0 to 1.0
    differential_diagnoses: List[Dict[str, float]]
    reasoning: Optional[str] = None
    algorithm_name: str = "External Evaluated Model"


class StressTestEvaluationResult(BaseModel):
    test_case_id: str
    algorithm_name: str
    is_top1_correct: bool
    is_top3_correct: bool
    ground_truth: str
    prediction: str
    confidence: float
    brier_score_contribution: float
    perturbation_summary: str
    robustness_score: float


# ============================================================================
# DIAGNOSTIC AI ADVERSARIAL ARENA SCHEMAS
# ============================================================================

class AppliedTransformation(BaseModel):
    transformation_type: str  # "MEASUREMENT_NOISE", "MISSING_LAB_DROPOUT", "ATYPICAL_AGE_SHIFT", "CONFOUNDING_INFECTION"
    feature_name: str
    original_value: Any
    perturbed_value: Any
    delta: Optional[str] = None
    unit: Optional[str] = None
    reason: str


class ConstraintValidationStatus(BaseModel):
    is_valid: bool = True
    status: str = "PASSED"  # "PASSED", "WARNING", "VIOLATED"
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: List[Dict[str, Any]] = Field(default_factory=list)


class DiagnosticPredictionResult(BaseModel):
    predicted_disease_id: str
    predicted_disease_name: str
    confidence_score: float  # 0.0 to 1.0
    differential_diagnoses: List[Dict[str, float]] = Field(default_factory=list)
    reasoning: Optional[str] = None
    algorithm_name: str
    is_top1_correct: bool
    is_top3_correct: bool = False
    evaluation_latency_ms: float = 0.0
    error_message: Optional[str] = None


class ArenaCaseRecord(BaseModel):
    case_id: str
    experiment_id: str
    original_patient_id: str
    disease_id: str
    disease_name: str
    seed: int
    perturbation_config: PerturbationConfig
    applied_transformations: List[AppliedTransformation] = Field(default_factory=list)
    constraint_validation: ConstraintValidationStatus
    evaluation_status: str  # "EVALUATED", "UNEVALUABLE", "REJECTED"
    failure_category: str  # "NONE", "INCORRECT_PREDICTION", "PREDICTION_INSTABILITY", "CONFIDENCE_COLLAPSE", "CONSTRAINT_VIOLATION", "UNEVALUABLE"
    is_failure: bool = False
    is_instability: bool = False
    baseline_prediction: Optional[DiagnosticPredictionResult] = None
    perturbed_prediction: Optional[DiagnosticPredictionResult] = None
    ground_truth_disease_id: str
    ground_truth_disease_name: str
    ground_truth_omim: str
    blinded_inputs: Dict[str, Any]
    original_inputs: Dict[str, Any]
    diff_summary: str
    model_name: Optional[str] = None
    evidence_provenance: List[str] = Field(default_factory=list)
    timestamp: str


class ArenaBenchmarkMetrics(BaseModel):
    total_cases_attempted: int
    valid_cases_count: int
    rejected_cases_count: int
    unevaluable_cases_count: int
    baseline_accuracy: Optional[float] = None
    perturbed_accuracy: Optional[float] = None
    accuracy_degradation: Optional[float] = None  # baseline_accuracy - perturbed_accuracy
    prediction_instability_rate: Optional[float] = None
    failure_count: int
    failure_rate: Optional[float] = None
    by_disease: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    by_perturbation_type: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    failure_breakdown: Dict[str, int] = Field(default_factory=dict)
    avg_confidence_baseline: Optional[float] = None
    avg_confidence_perturbed: Optional[float] = None


class ArenaExperimentConfig(BaseModel):
    disease_selection: str = "all"  # "wilson_disease", "fabry_disease", "gaucher_disease", "all"
    num_cases_per_disease: int = 5
    random_seed: int = 42
    model_type: str = "reference_baseline"  # "reference_baseline", "mock_fragile", "mock_robust", "external_http"
    external_endpoint_url: Optional[str] = None
    search_strategy: str = "sweep"  # "sweep", "adversarial_search", "repeated_variants"
    perturbation_categories: List[str] = Field(
        default_factory=lambda: ["measurement_noise", "missing_labs", "atypical_age", "confounding_infection"]
    )
    noise_sigma: float = 0.15
    missing_lab_rate: float = 0.25
    atypical_age_shift_years: int = 0
    inject_confounding_infection: bool = False
    max_cases: int = 50


class ArenaExperimentResult(BaseModel):
    experiment_id: str
    config: ArenaExperimentConfig
    created_at: str
    status: str  # "COMPLETED", "FAILED"
    metrics: ArenaBenchmarkMetrics
    cases: List[ArenaCaseRecord] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ArenaCapabilityInfo(BaseModel):
    supported_diseases: List[Dict[str, str]]
    supported_perturbations: List[Dict[str, Any]]
    supported_models: List[Dict[str, str]]
    search_strategies: List[Dict[str, str]]
    hard_constraints_summary: List[Dict[str, Any]]
    disclaimer: str


# ============================================================================
# BREAKING POINT FINDER SCHEMAS
# ============================================================================

class BreakingPointSearchConfig(BaseModel):
    disease_id: str = "wilson_disease"
    patient_id: Optional[str] = None
    random_seed: int = 42
    model_type: str = "mock_fragile"  # "mock_fragile", "reference_baseline", "mock_robust", "external_http"
    external_endpoint_url: Optional[str] = None
    search_axis: str = "noise_sigma"  # "noise_sigma", "missing_labs", "age_shift", "confounding_infection", "adaptive_combined"
    max_steps: int = 15
    step_size: float = 0.02
    target_failure_type: str = "ANY"  # "ANY", "MISDIAGNOSIS", "CONFIDENCE_COLLAPSE"
    confidence_collapse_threshold: float = 0.50


class BreakingPointStepRecord(BaseModel):
    step_index: int
    parameter_value: float
    parameter_label: str
    perturbation_summary: str
    is_clinically_valid: bool
    validation_status: str
    predicted_disease_id: str
    predicted_disease_name: str
    confidence_score: float
    is_top1_correct: bool
    is_breaking_point: bool
    failure_mode: Optional[str] = None  # None, "MISDIAGNOSIS", "CONFIDENCE_COLLAPSE"


class BreakingPointResult(BaseModel):
    search_id: str
    model_name: str
    disease_id: str
    disease_name: str
    patient_id: str
    search_axis: str
    breaking_point_found: bool
    minimal_delta: Optional[Dict[str, Any]] = None
    failure_type: Optional[str] = None
    baseline_prediction: Optional[DiagnosticPredictionResult] = None
    breaking_prediction: Optional[DiagnosticPredictionResult] = None
    steps_evaluated: int
    step_history: List[BreakingPointStepRecord] = Field(default_factory=list)
    affected_features: List[AppliedTransformation] = Field(default_factory=list)
    clinical_interpretation: str = ""
    created_at: str = ""


class BreakingPointComparisonConfig(BaseModel):
    disease_id: str = "wilson_disease"
    patient_id: Optional[str] = None
    random_seed: int = 42
    models: List[str] = Field(default_factory=lambda: ["mock_fragile", "reference_baseline", "mock_robust"])
    external_endpoint_url: Optional[str] = None
    search_axis: str = "noise_sigma"
    max_steps: int = 15
    step_size: float = 0.02


class BreakingPointComparisonReport(BaseModel):
    comparison_id: str
    disease_id: str
    disease_name: str
    search_axis: str
    results: Dict[str, BreakingPointResult] = Field(default_factory=dict)
    resilience_ranking: List[Dict[str, Any]] = Field(default_factory=list)
    comparative_summary: str = ""
    created_at: str = ""

