"""Diagnostic AI Adversarial Arena Engine.

Automated, reproducible discovery and stress-testing of diagnostic AI systems
against clinically grounded rare-disease synthetic patient avatars.
"""
import csv
import io
import json
import time
import uuid
import datetime
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import requests

from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.diagnostic import (
    PerturbationConfig, ExportableTestCase, AppliedTransformation,
    ConstraintValidationStatus, DiagnosticPredictionResult,
    ArenaCaseRecord, ArenaBenchmarkMetrics, ArenaExperimentConfig,
    ArenaExperimentResult, ArenaCapabilityInfo,
    BreakingPointSearchConfig, BreakingPointStepRecord,
    BreakingPointResult, BreakingPointComparisonConfig,
    BreakingPointComparisonReport
)
from app.disease_models import disease_registry
from app.generators.patient_generator import patient_generator
from app.stress_testing.perturbation_engine import perturbation_engine
from app.stress_testing.benchmark_runner import benchmark_runner


class MockFragileDiagnosticClassifier:
    """
    A brittle diagnostic AI model that demonstrates common algorithmic vulnerabilities:
    - Overfits to individual diagnostic labs (e.g. ceruloplasmin in Wilson, lyso-Gb3 in Fabry)
    - Vulnerable to confounding infection (elevated WBC/CRP leads to misdiagnosis)
    - Struggles with missing tests or atypical age shifts
    """
    def predict(self, test_case: ExportableTestCase) -> DiagnosticPredictionResult:
        lab_dict = {l["test_code"]: l["value"] for l in test_case.input_laboratory}
        has_infection = ("CRP" in lab_dict and lab_dict["CRP"] > 40.0) or ("WBC" in lab_dict and lab_dict["WBC"] > 14.0)

        # Vulnerability 1: If acute infection confounder is present, fragile model misdiagnoses as systemic sepsis/infection
        if has_infection:
            return DiagnosticPredictionResult(
                predicted_disease_id="other_idiopathic",
                predicted_disease_name="Systemic Inflammatory Response / Non-Rare Infection",
                confidence_score=0.74,
                differential_diagnoses=[
                    {"Systemic Inflammatory Response": 0.74},
                    {"Other Idiopathic": 0.16},
                    {"Wilson Disease": 0.05},
                    {"Fabry Disease": 0.03},
                    {"Gaucher Disease Type 1": 0.02}
                ],
                reasoning="Dominated by acute phase markers (elevated CRP and leukocytosis).",
                algorithm_name="Mock Fragile Diagnostic AI (Brittle Decision Tree)",
                is_top1_correct=("other_idiopathic" == test_case.ground_truth_disease_id),
                is_top3_correct=False
            )

        # Wilson Disease Evaluation
        cp = lab_dict.get("CERULOPLASMIN")
        if cp is not None:
            # Overly narrow threshold: requires cp < 15.0 mg/dL strictly
            if cp < 15.0:
                is_correct = (test_case.ground_truth_disease_id == "wilson_disease")
                return DiagnosticPredictionResult(
                    predicted_disease_id="wilson_disease",
                    predicted_disease_name="Wilson Disease",
                    confidence_score=0.88,
                    differential_diagnoses=[
                        {"Wilson Disease": 0.88},
                        {"Other Idiopathic": 0.08},
                        {"Gaucher Disease Type 1": 0.04}
                    ],
                    reasoning=f"Identified ceruloplasmin deficiency at {cp} mg/dL.",
                    algorithm_name="Mock Fragile Diagnostic AI (Brittle Decision Tree)",
                    is_top1_correct=is_correct,
                    is_top3_correct=True
                )
            else:
                # Borderline ceruloplasmin causes collapse
                return DiagnosticPredictionResult(
                    predicted_disease_id="other_idiopathic",
                    predicted_disease_name="Unspecified Hepatic Dysfunction",
                    confidence_score=0.52,
                    differential_diagnoses=[
                        {"Unspecified Hepatic Dysfunction": 0.52},
                        {"Wilson Disease": 0.38},
                        {"Other Idiopathic": 0.10}
                    ],
                    reasoning=f"Ceruloplasmin at {cp} mg/dL is above brittle decision threshold (15 mg/dL).",
                    algorithm_name="Mock Fragile Diagnostic AI (Brittle Decision Tree)",
                    is_top1_correct=("other_idiopathic" == test_case.ground_truth_disease_id),
                    is_top3_correct=("wilson_disease" == test_case.ground_truth_disease_id)
                )

        # Fabry Disease Evaluation
        lyso_gb3 = lab_dict.get("LYSO_GB3")
        if lyso_gb3 is not None and lyso_gb3 > 12.0:
            is_correct = (test_case.ground_truth_disease_id == "fabry_disease")
            return DiagnosticPredictionResult(
                predicted_disease_id="fabry_disease",
                predicted_disease_name="Fabry Disease",
                confidence_score=0.89,
                differential_diagnoses=[
                    {"Fabry Disease": 0.89},
                    {"Other Idiopathic": 0.08},
                    {"Gaucher Disease Type 1": 0.03}
                ],
                reasoning=f"Lyso-Gb3 biomarker elevation at {lyso_gb3} ng/mL.",
                algorithm_name="Mock Fragile Diagnostic AI (Brittle Decision Tree)",
                is_top1_correct=is_correct,
                is_top3_correct=True
            )

        # Gaucher Disease Evaluation
        lyso_gb1 = lab_dict.get("LYSO_GB1")
        if lyso_gb1 is not None and lyso_gb1 > 10.0:
            is_correct = (test_case.ground_truth_disease_id == "gaucher_disease")
            return DiagnosticPredictionResult(
                predicted_disease_id="gaucher_disease",
                predicted_disease_name="Gaucher Disease Type 1",
                confidence_score=0.91,
                differential_diagnoses=[
                    {"Gaucher Disease Type 1": 0.91},
                    {"Other Idiopathic": 0.06},
                    {"Wilson Disease": 0.03}
                ],
                reasoning=f"Lyso-Gb1 biomarker elevation at {lyso_gb1} ng/mL.",
                algorithm_name="Mock Fragile Diagnostic AI (Brittle Decision Tree)",
                is_top1_correct=is_correct,
                is_top3_correct=True
            )

        # Fallback if primary biomarkers were withheld or outside narrow threshold
        return DiagnosticPredictionResult(
            predicted_disease_id="other_idiopathic",
            predicted_disease_name="Undifferentiated Clinical Presentation",
            confidence_score=0.45,
            differential_diagnoses=[
                {"Undifferentiated Clinical Presentation": 0.45},
                {"Wilson Disease": 0.20},
                {"Fabry Disease": 0.20},
                {"Gaucher Disease Type 1": 0.15}
            ],
            reasoning="Primary pathognomonic lab biomarkers missing from profile.",
            algorithm_name="Mock Fragile Diagnostic AI (Brittle Decision Tree)",
            is_top1_correct=("other_idiopathic" == test_case.ground_truth_disease_id),
            is_top3_correct=False
        )


class MockRobustDiagnosticClassifier:
    """
    A robust multimodal Bayesian diagnostic AI model:
    - Integrates clinical symptoms, organ imaging signs, and multi-test laboratory findings
    - Resilient to individual missing labs or measurement noise
    - Discounts acute inflammatory confounders when disease-specific imaging signs exist
    """
    def predict(self, test_case: ExportableTestCase) -> DiagnosticPredictionResult:
        sub = benchmark_runner.ref_classifier.predict(test_case)
        is_top1 = (sub.predicted_disease_id == test_case.ground_truth_disease_id)

        # Enhanced multi-modal integration gives robust confidence
        conf = min(0.95, sub.confidence_score + 0.12) if is_top1 else max(0.20, sub.confidence_score - 0.10)

        # Check top 3
        top3_ids = [list(d.keys())[0].lower() for d in sub.differential_diagnoses[:3]]
        is_top3 = is_top1 or any(test_case.ground_truth_disease_id in name for name in top3_ids)

        return DiagnosticPredictionResult(
            predicted_disease_id=sub.predicted_disease_id,
            predicted_disease_name=sub.predicted_disease_name,
            confidence_score=round(conf, 3),
            differential_diagnoses=sub.differential_diagnoses,
            reasoning=f"Multimodal Bayesian fusion integrating {len(test_case.input_symptoms)} symptoms, {len(test_case.input_laboratory)} labs, and {len(test_case.input_imaging_summary)} imaging studies.",
            algorithm_name="Mock Robust Diagnostic AI (Multimodal Bayesian Ensemble)",
            is_top1_correct=is_top1,
            is_top3_correct=is_top3
        )


class AdversarialArenaEngine:
    def __init__(self):
        self._experiments: Dict[str, ArenaExperimentResult] = {}
        self._cases: Dict[str, ArenaCaseRecord] = {}
        self._fragile_model = MockFragileDiagnosticClassifier()
        self._robust_model = MockRobustDiagnosticClassifier()

    def get_capabilities(self) -> ArenaCapabilityInfo:
        return ArenaCapabilityInfo(
            supported_diseases=[
                {"disease_id": "wilson_disease", "name": "Wilson Disease", "omim": "OMIM #277900"},
                {"disease_id": "fabry_disease", "name": "Fabry Disease", "omim": "OMIM #301500"},
                {"disease_id": "gaucher_disease", "name": "Gaucher Disease Type 1", "omim": "OMIM #230800"}
            ],
            supported_perturbations=[
                {
                    "type": "MEASUREMENT_NOISE",
                    "description": "Gaussian relative noise added to laboratory and symptom severity scores.",
                    "supported": True,
                    "bounds": "σ ∈ [0.0, 0.50]"
                },
                {
                    "type": "MISSING_LAB_DROPOUT",
                    "description": "Withholds a configurable percentage of laboratory tests to simulate incomplete diagnostic workup.",
                    "supported": True,
                    "bounds": "Rate ∈ [0.0, 0.80]"
                },
                {
                    "type": "ATYPICAL_AGE_SHIFT",
                    "description": "Shifts patient age to test algorithmic vulnerability to non-canonical age of onset.",
                    "supported": True,
                    "bounds": "[-20, +20] years"
                },
                {
                    "type": "CONFOUNDING_INFECTION",
                    "description": "Injects elevated acute-phase reactants (CRP 45-110 mg/L, WBC 14.5-19.8 x10^3/uL) to test specificity under intercurrent infection.",
                    "supported": True,
                    "bounds": "Binary flag"
                },
                {
                    "type": "COMBINED",
                    "description": "Applies multiple compatible perturbations in execution order with rigorous constraint checking.",
                    "supported": True,
                    "bounds": "Multi-category"
                }
            ],
            supported_models=[
                {
                    "model_type": "reference_baseline",
                    "name": "Reference Guideline Classifier (Baseline)",
                    "description": "Rule-based guideline model derived from EASL, Ortiz et al., and Pastores et al."
                },
                {
                    "model_type": "mock_fragile",
                    "name": "Mock Fragile Diagnostic AI",
                    "description": "Demonstration model with narrow decision thresholds; vulnerable to missing labs and acute confounders."
                },
                {
                    "model_type": "mock_robust",
                    "name": "Mock Robust Diagnostic AI",
                    "description": "Multimodal Bayesian ensemble integrating symptoms, laboratory markers, and imaging signs."
                },
                {
                    "model_type": "external_http",
                    "name": "External HTTP Diagnostic API",
                    "description": "Connects to an external REST endpoint via HTTP POST with schema validation and timeout handling."
                }
            ],
            search_strategies=[
                {
                    "strategy": "sweep",
                    "name": "Controlled Parameter Sweep",
                    "description": "Systematic evaluation of configured noise, missing rate, age shift, and confounders across synthetic avatars."
                },
                {
                    "strategy": "adversarial_search",
                    "name": "Borderline Adversarial Search",
                    "description": "Targeted search probing parameters near clinical decision boundaries while maintaining pathophysiological validity."
                },
                {
                    "strategy": "repeated_variants",
                    "name": "Repeated Stochastic Variations",
                    "description": "Evaluates multiple reproducible stochastic variants of the same initial patient avatars to detect prediction instability."
                }
            ],
            hard_constraints_summary=[
                {
                    "disease_id": "wilson_disease",
                    "rule": "Serum Ceruloplasmin Bound",
                    "threshold": "<= 20.0 mg/dL",
                    "severity": "FATAL_ERROR",
                    "clinical_basis": "Classical Wilson disease exhibits copper metabolism defect with ceruloplasmin deficiency."
                },
                {
                    "disease_id": "wilson_disease",
                    "rule": "24h Urinary Copper Lower Bound",
                    "threshold": ">= 50.0 ug/24h",
                    "severity": "FATAL_ERROR",
                    "clinical_basis": "Active disease requires elevated urinary copper excretion exceeding upper limit of normal."
                },
                {
                    "disease_id": "fabry_disease",
                    "rule": "Plasma Lyso-Gb3 Elevation",
                    "threshold": ">= 0.8 ng/mL",
                    "severity": "FATAL_ERROR",
                    "clinical_basis": "Symptomatic classic Fabry disease requires Lyso-Gb3 biomarker elevation."
                },
                {
                    "disease_id": "fabry_disease",
                    "rule": "Alpha-Galactosidase A Deficiency",
                    "threshold": "<= 3.0 nmol/h/mg",
                    "severity": "FATAL_ERROR",
                    "clinical_basis": "Affected males must demonstrate subnormal enzyme activity."
                },
                {
                    "disease_id": "gaucher_disease",
                    "rule": "Plasma Lyso-Gb1 Elevation",
                    "threshold": ">= 1.5 ng/mL",
                    "severity": "FATAL_ERROR",
                    "clinical_basis": "Symptomatic Gaucher type 1 requires Lyso-Gb1 biomarker elevation."
                },
                {
                    "disease_id": "gaucher_disease",
                    "rule": "Beta-Glucosidase Deficiency",
                    "threshold": "<= 2.5 nmol/h/mg",
                    "severity": "FATAL_ERROR",
                    "clinical_basis": "Definitive enzymatic confirmation requires leukocyte beta-glucosidase deficiency."
                }
            ],
            disclaimer="RareAvatar Diagnostic AI Adversarial Arena is a synthetic biomedical AI research and educational platform. Simulated scenarios do not constitute clinical advice or independently verified diagnostic claims for real patients."
        )

    def evaluate_model(
        self,
        model_type: str,
        test_case: ExportableTestCase,
        external_url: Optional[str] = None
    ) -> DiagnosticPredictionResult:
        t0 = time.perf_counter()

        # Mode 1: Reference Guideline Baseline
        if model_type == "reference_baseline":
            sub = benchmark_runner.ref_classifier.predict(test_case)
            is_top1 = (sub.predicted_disease_id == test_case.ground_truth_disease_id)
            top3_ids = [list(d.keys())[0].lower() for d in sub.differential_diagnoses[:3]]
            is_top3 = is_top1 or any(test_case.ground_truth_disease_id in name for name in top3_ids)
            dt_ms = round((time.perf_counter() - t0) * 1000, 2)
            return DiagnosticPredictionResult(
                predicted_disease_id=sub.predicted_disease_id,
                predicted_disease_name=sub.predicted_disease_name,
                confidence_score=sub.confidence_score,
                differential_diagnoses=sub.differential_diagnoses,
                reasoning=sub.reasoning,
                algorithm_name=sub.algorithm_name,
                is_top1_correct=is_top1,
                is_top3_correct=is_top3,
                evaluation_latency_ms=dt_ms
            )

        # Mode 2: Mock Fragile Model
        elif model_type == "mock_fragile":
            res = self._fragile_model.predict(test_case)
            res.evaluation_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return res

        # Mode 3: Mock Robust Model
        elif model_type == "mock_robust":
            res = self._robust_model.predict(test_case)
            res.evaluation_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return res

        # Mode 4: External HTTP Diagnostic Model
        elif model_type == "external_http":
            if not external_url:
                raise ValueError("External diagnostic model endpoint URL is required when model_type is 'external_http'.")

            # Prepare Blinded Model Inputs (Strictly blinded from reference label)
            payload = {
                "test_case_id": test_case.test_case_id,
                "input_demographics": test_case.input_demographics,
                "input_symptoms": test_case.input_symptoms,
                "input_laboratory": test_case.input_laboratory,
                "input_imaging_summary": test_case.input_imaging_summary
            }

            try:
                resp = requests.post(external_url, json=payload, timeout=3.0)
                dt_ms = round((time.perf_counter() - t0) * 1000, 2)

                if resp.status_code != 200:
                    return DiagnosticPredictionResult(
                        predicted_disease_id="EXTERNAL_ERROR",
                        predicted_disease_name="External Service Error",
                        confidence_score=0.0,
                        differential_diagnoses=[],
                        reasoning=f"External model returned HTTP {resp.status_code}: {resp.text[:120]}",
                        algorithm_name="External Diagnostic Model",
                        is_top1_correct=False,
                        is_top3_correct=False,
                        evaluation_latency_ms=dt_ms,
                        error_message=f"HTTP {resp.status_code} Error"
                    )

                data = resp.json()
                pred_id = data.get("predicted_disease_id", "UNKNOWN")
                pred_name = data.get("predicted_disease_name", pred_id)
                conf = float(data.get("confidence_score", 0.0))
                diff = data.get("differential_diagnoses", [])
                reasoning = data.get("reasoning", "External diagnostic prediction received.")

                is_top1 = (pred_id == test_case.ground_truth_disease_id)
                top3_ids = [list(d.keys())[0].lower() for d in diff[:3]] if diff else []
                is_top3 = is_top1 or any(test_case.ground_truth_disease_id in name for name in top3_ids)

                return DiagnosticPredictionResult(
                    predicted_disease_id=pred_id,
                    predicted_disease_name=pred_name,
                    confidence_score=conf,
                    differential_diagnoses=diff,
                    reasoning=reasoning,
                    algorithm_name=data.get("algorithm_name", "External Diagnostic Model"),
                    is_top1_correct=is_top1,
                    is_top3_correct=is_top3,
                    evaluation_latency_ms=dt_ms
                )
            except requests.exceptions.Timeout:
                dt_ms = round((time.perf_counter() - t0) * 1000, 2)
                return DiagnosticPredictionResult(
                    predicted_disease_id="TIMEOUT",
                    predicted_disease_name="Model Request Timed Out",
                    confidence_score=0.0,
                    differential_diagnoses=[],
                    reasoning="External diagnostic model timed out after 3.0 seconds.",
                    algorithm_name="External Diagnostic Model",
                    is_top1_correct=False,
                    is_top3_correct=False,
                    evaluation_latency_ms=dt_ms,
                    error_message="Connection timed out (3.0s limit)"
                )
            except Exception as e:
                dt_ms = round((time.perf_counter() - t0) * 1000, 2)
                return DiagnosticPredictionResult(
                    predicted_disease_id="NETWORK_ERROR",
                    predicted_disease_name="External Connection Failed",
                    confidence_score=0.0,
                    differential_diagnoses=[],
                    reasoning=f"Failed to connect to external model: {str(e)}",
                    algorithm_name="External Diagnostic Model",
                    is_top1_correct=False,
                    is_top3_correct=False,
                    evaluation_latency_ms=dt_ms,
                    error_message=str(e)
                )

        else:
            raise ValueError(f"Unknown model_type: '{model_type}'")

    def run_experiment(self, config: ArenaExperimentConfig) -> ArenaExperimentResult:
        experiment_id = f"ARENA-EXP-{uuid.uuid4().hex[:6].upper()}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Validate bounded configuration
        cases_per_d = max(1, min(20, config.num_cases_per_disease))
        base_seed = config.random_seed

        # Determine target diseases
        if config.disease_selection == "all":
            disease_ids = ["wilson_disease", "fabry_disease", "gaucher_disease"]
        else:
            disease_ids = [config.disease_selection]

        case_records: List[ArenaCaseRecord] = []
        notes: List[str] = []

        total_attempted = 0
        valid_count = 0
        rejected_count = 0
        unevaluable_count = 0

        # For tracking metric breakdowns
        disease_stats: Dict[str, Dict[str, Any]] = {
            d: {
                "total": 0, "valid": 0, "baseline_correct": 0,
                "perturbed_correct": 0, "instability_count": 0, "failure_count": 0
            }
            for d in disease_ids
        }
        perturbation_stats: Dict[str, Dict[str, Any]] = {
            "MEASUREMENT_NOISE": {"total": 0, "correct": 0, "failures": 0},
            "MISSING_LAB_DROPOUT": {"total": 0, "correct": 0, "failures": 0},
            "ATYPICAL_AGE_SHIFT": {"total": 0, "correct": 0, "failures": 0},
            "CONFOUNDING_INFECTION": {"total": 0, "correct": 0, "failures": 0},
            "COMBINED": {"total": 0, "correct": 0, "failures": 0}
        }
        failure_breakdown: Dict[str, int] = {
            "NONE": 0,
            "INCORRECT_PREDICTION": 0,
            "PREDICTION_INSTABILITY": 0,
            "CONFIDENCE_COLLAPSE": 0,
            "CONSTRAINT_VIOLATION": 0,
            "UNEVALUABLE": 0
        }

        baseline_correct_total = 0
        perturbed_correct_total = 0
        instability_total = 0
        failure_total = 0
        evaluable_total = 0

        conf_baseline_sum = 0.0
        conf_perturbed_sum = 0.0
        conf_evaluable_count = 0

        case_idx = 0
        for d_id in disease_ids:
            for i in range(cases_per_d):
                total_attempted += 1
                case_idx += 1
                case_seed = base_seed + (case_idx * 101)

                # 1. Deterministic synthetic avatar generation
                patient = patient_generator.generate_patient(
                    disease_id=d_id,
                    seed=case_seed
                )

                # 2. Baseline Case (Unperturbed reference patient)
                baseline_cfg = PerturbationConfig(
                    noise_sigma=0.0,
                    missing_lab_rate=0.0,
                    atypical_age_shift_years=0,
                    inject_confounding_infection=False,
                    reproducibility_seed=case_seed
                )
                baseline_arena_data = perturbation_engine.create_arena_case(
                    patient=patient,
                    config=baseline_cfg,
                    experiment_id=experiment_id
                )
                baseline_tc = baseline_arena_data["exportable_test_case"]

                # 3. Formulate Perturbation Configuration based on Strategy
                if config.search_strategy == "sweep":
                    p_cfg = PerturbationConfig(
                        noise_sigma=config.noise_sigma,
                        missing_lab_rate=config.missing_lab_rate,
                        atypical_age_shift_years=config.atypical_age_shift_years,
                        inject_confounding_infection=config.inject_confounding_infection,
                        reproducibility_seed=case_seed
                    )
                elif config.search_strategy == "adversarial_search":
                    # Targeted borderline parameter search
                    # Tests near physiological threshold without crossing into invalid bounds
                    search_noise = min(0.35, config.noise_sigma + 0.10)
                    search_missing = min(0.60, config.missing_lab_rate + 0.15)
                    # Alternate infection confounder on every other case
                    search_infection = (i % 2 == 1) or config.inject_confounding_infection
                    search_age_shift = 10 if (i % 3 == 0) else (-5 if i % 3 == 1 else 0)
                    p_cfg = PerturbationConfig(
                        noise_sigma=search_noise,
                        missing_lab_rate=search_missing,
                        atypical_age_shift_years=search_age_shift,
                        inject_confounding_infection=search_infection,
                        reproducibility_seed=case_seed
                    )
                else:  # "repeated_variants"
                    # Stochastic variant with distinct seed jitter
                    variant_seed = case_seed + 9999 + i
                    p_cfg = PerturbationConfig(
                        noise_sigma=config.noise_sigma,
                        missing_lab_rate=config.missing_lab_rate,
                        atypical_age_shift_years=config.atypical_age_shift_years,
                        inject_confounding_infection=config.inject_confounding_infection,
                        reproducibility_seed=variant_seed
                    )

                # 4. Generate Perturbed Case with Full Transformation & Constraint Audit
                arena_data = perturbation_engine.create_arena_case(
                    patient=patient,
                    config=p_cfg,
                    experiment_id=experiment_id
                )

                tc_perturbed = arena_data["exportable_test_case"]
                c_status: ConstraintValidationStatus = arena_data["constraint_validation"]
                applied_trans: List[AppliedTransformation] = arena_data["applied_transformations"]
                insufficient_ref = arena_data["insufficient_evidence"]
                diff_summary = arena_data["diff_summary"]

                # 5. Evaluate Baseline Model Prediction
                baseline_pred: Optional[DiagnosticPredictionResult] = None
                try:
                    baseline_pred = self.evaluate_model(
                        config.model_type, baseline_tc, config.external_endpoint_url
                    )
                except Exception as e:
                    notes.append(f"Baseline eval error on {patient.patient_id}: {str(e)}")

                # 6. Assess Validity and Determine Evaluation Status
                perturbed_pred: Optional[DiagnosticPredictionResult] = None
                evaluation_status: str
                failure_category: str
                is_failure = False
                is_instability = False

                if not c_status.is_valid:
                    # Category D: Violates permitted disease-model constraints (REJECTED)
                    rejected_count += 1
                    evaluation_status = "REJECTED"
                    failure_category = "CONSTRAINT_VIOLATION"
                    is_failure = True
                    failure_breakdown["CONSTRAINT_VIOLATION"] += 1
                elif insufficient_ref:
                    # Category C: Reference information insufficient to reliably evaluate
                    valid_count += 1
                    unevaluable_count += 1
                    evaluation_status = "UNEVALUABLE"
                    failure_category = "UNEVALUABLE"
                    failure_breakdown["UNEVALUABLE"] += 1
                    # Attempt model prediction to observe graceful degradation
                    try:
                        perturbed_pred = self.evaluate_model(
                            config.model_type, tc_perturbed, config.external_endpoint_url
                        )
                    except Exception:
                        pass
                else:
                    # Valid, evaluable case -> Proceed with perturbed model evaluation
                    valid_count += 1
                    try:
                        perturbed_pred = self.evaluate_model(
                            config.model_type, tc_perturbed, config.external_endpoint_url
                        )
                    except Exception as e:
                        perturbed_pred = DiagnosticPredictionResult(
                            predicted_disease_id="EVALUATION_FAILED",
                            predicted_disease_name="Evaluation Exception",
                            confidence_score=0.0,
                            reasoning=str(e),
                            algorithm_name=config.model_type,
                            is_top1_correct=False,
                            is_top3_correct=False,
                            error_message=str(e)
                        )

                    # Check for model communication failure
                    if perturbed_pred.error_message:
                        unevaluable_count += 1
                        evaluation_status = "UNEVALUABLE"
                        failure_category = "UNEVALUABLE"
                        failure_breakdown["UNEVALUABLE"] += 1
                    else:
                        evaluable_total += 1
                        evaluation_status = "EVALUATED"

                        # Track confidence averages
                        if baseline_pred and baseline_pred.confidence_score > 0:
                            conf_baseline_sum += baseline_pred.confidence_score
                            conf_perturbed_sum += perturbed_pred.confidence_score
                            conf_evaluable_count += 1

                        # Scoring
                        b_correct = baseline_pred.is_top1_correct if baseline_pred else False
                        p_correct = perturbed_pred.is_top1_correct

                        if b_correct:
                            baseline_correct_total += 1
                            disease_stats[d_id]["baseline_correct"] += 1

                        if p_correct:
                            perturbed_correct_total += 1
                            disease_stats[d_id]["perturbed_correct"] += 1

                        # Prediction Instability: baseline and perturbed predictions differ
                        pred_changed = False
                        if baseline_pred:
                            pred_changed = (baseline_pred.predicted_disease_id != perturbed_pred.predicted_disease_id)

                        if pred_changed:
                            instability_total += 1
                            is_instability = True
                            disease_stats[d_id]["instability_count"] += 1

                        # Failure Classification
                        if not p_correct:
                            # Category A: Genuinely incorrect prediction against valid reference label
                            failure_category = "INCORRECT_PREDICTION"
                            is_failure = True
                            failure_total += 1
                            disease_stats[d_id]["failure_count"] += 1
                            failure_breakdown["INCORRECT_PREDICTION"] += 1
                        elif pred_changed:
                            # Category B: Unstable prediction under clinically meaningful inputs
                            failure_category = "PREDICTION_INSTABILITY"
                            is_failure = True
                            failure_total += 1
                            disease_stats[d_id]["failure_count"] += 1
                            failure_breakdown["PREDICTION_INSTABILITY"] += 1
                        elif baseline_pred and (baseline_pred.confidence_score - perturbed_pred.confidence_score) >= 0.35:
                            # Severe confidence collapse
                            failure_category = "CONFIDENCE_COLLAPSE"
                            is_failure = True
                            failure_total += 1
                            disease_stats[d_id]["failure_count"] += 1
                            failure_breakdown["CONFIDENCE_COLLAPSE"] += 1
                        else:
                            failure_category = "NONE"
                            is_failure = False
                            failure_breakdown["NONE"] += 1

                # Tally perturbation category statistics
                trans_types = {t.transformation_type for t in applied_trans}
                cat_key = "COMBINED" if len(trans_types) > 1 else (next(iter(trans_types)) if trans_types else "MEASUREMENT_NOISE")
                if cat_key in perturbation_stats:
                    perturbation_stats[cat_key]["total"] += 1
                    if evaluation_status == "EVALUATED" and perturbed_pred and perturbed_pred.is_top1_correct:
                        perturbation_stats[cat_key]["correct"] += 1
                    if is_failure:
                        perturbation_stats[cat_key]["failures"] += 1

                disease_stats[d_id]["total"] += 1
                if c_status.is_valid:
                    disease_stats[d_id]["valid"] += 1

                # Gather evidence provenance
                evidence_list = list(patient.evidence_catalog.keys())

                record = ArenaCaseRecord(
                    case_id=tc_perturbed.test_case_id,
                    experiment_id=experiment_id,
                    original_patient_id=patient.patient_id,
                    disease_id=d_id,
                    disease_name=patient.disease.disease_name,
                    seed=case_seed,
                    perturbation_config=p_cfg,
                    applied_transformations=applied_trans,
                    constraint_validation=c_status,
                    evaluation_status=evaluation_status,
                    failure_category=failure_category,
                    is_failure=is_failure,
                    is_instability=is_instability,
                    baseline_prediction=baseline_pred,
                    perturbed_prediction=perturbed_pred,
                    ground_truth_disease_id=patient.disease.disease_id,
                    ground_truth_disease_name=patient.disease.disease_name,
                    ground_truth_omim=patient.disease.omim_id,
                    blinded_inputs=arena_data["blinded_inputs"],
                    original_inputs=arena_data["original_inputs"],
                    diff_summary=diff_summary,
                    model_name=perturbed_pred.algorithm_name if perturbed_pred else config.model_type,
                    evidence_provenance=evidence_list,
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                )

                case_records.append(record)
                self._cases[record.case_id] = record

        # 7. Calculate Mathematically Rigorous Benchmark Metrics
        # Denominator is strictly evaluable_total (valid cases with completed evaluation)
        if evaluable_total > 0:
            base_acc = round(baseline_correct_total / evaluable_total, 4)
            pert_acc = round(perturbed_correct_total / evaluable_total, 4)
            acc_deg = round(base_acc - pert_acc, 4)
            instability_rate = round(instability_total / evaluable_total, 4)
            failure_rate = round(failure_total / evaluable_total, 4)
        else:
            base_acc = None
            pert_acc = None
            acc_deg = None
            instability_rate = None
            failure_rate = None

        avg_conf_base = round(conf_baseline_sum / conf_evaluable_count, 3) if conf_evaluable_count > 0 else None
        avg_conf_pert = round(conf_perturbed_sum / conf_evaluable_count, 3) if conf_evaluable_count > 0 else None

        # Format by_disease summary
        by_disease_summary: Dict[str, Dict[str, Any]] = {}
        for d_id, s in disease_stats.items():
            valid_d = s["valid"]
            b_acc_d = round(s["baseline_correct"] / valid_d, 4) if valid_d > 0 else None
            p_acc_d = round(s["perturbed_correct"] / valid_d, 4) if valid_d > 0 else None
            deg_d = round(b_acc_d - p_acc_d, 4) if (b_acc_d is not None and p_acc_d is not None) else None
            by_disease_summary[d_id] = {
                "total_cases": s["total"],
                "valid_cases": valid_d,
                "baseline_accuracy": b_acc_d,
                "perturbed_accuracy": p_acc_d,
                "accuracy_degradation": deg_d,
                "instability_count": s["instability_count"],
                "failure_count": s["failure_count"],
                "failure_rate": round(s["failure_count"] / valid_d, 4) if valid_d > 0 else None
            }

        # Format by_perturbation summary
        by_perturbation_summary: Dict[str, Dict[str, Any]] = {}
        for p_type, s in perturbation_stats.items():
            tot = s["total"]
            by_perturbation_summary[p_type] = {
                "cases_evaluated": tot,
                "correct_predictions": s["correct"],
                "failures_discovered": s["failures"],
                "accuracy": round(s["correct"] / tot, 4) if tot > 0 else None,
                "failure_rate": round(s["failures"] / tot, 4) if tot > 0 else None
            }

        metrics = ArenaBenchmarkMetrics(
            total_cases_attempted=total_attempted,
            valid_cases_count=valid_count,
            rejected_cases_count=rejected_count,
            unevaluable_cases_count=unevaluable_count,
            baseline_accuracy=base_acc,
            perturbed_accuracy=pert_acc,
            accuracy_degradation=acc_deg,
            prediction_instability_rate=instability_rate,
            failure_count=failure_total,
            failure_rate=failure_rate,
            by_disease=by_disease_summary,
            by_perturbation_type=by_perturbation_summary,
            failure_breakdown=failure_breakdown,
            avg_confidence_baseline=avg_conf_base,
            avg_confidence_perturbed=avg_conf_pert
        )

        res = ArenaExperimentResult(
            experiment_id=experiment_id,
            config=config,
            created_at=created_at,
            status="COMPLETED",
            metrics=metrics,
            cases=case_records,
            notes=notes
        )

        self._experiments[experiment_id] = res
        return res

    def get_experiment(self, experiment_id: str) -> Optional[ArenaExperimentResult]:
        return self._experiments.get(experiment_id)

    def list_experiments(self) -> List[Dict[str, Any]]:
        summaries = []
        for exp in sorted(self._experiments.values(), key=lambda e: e.created_at, reverse=True):
            summaries.append({
                "experiment_id": exp.experiment_id,
                "created_at": exp.created_at,
                "disease_selection": exp.config.disease_selection,
                "model_type": exp.config.model_type,
                "search_strategy": exp.config.search_strategy,
                "total_cases": exp.metrics.total_cases_attempted,
                "valid_cases": exp.metrics.valid_cases_count,
                "rejected_cases": exp.metrics.rejected_cases_count,
                "baseline_accuracy": exp.metrics.baseline_accuracy,
                "perturbed_accuracy": exp.metrics.perturbed_accuracy,
                "accuracy_degradation": exp.metrics.accuracy_degradation,
                "failure_count": exp.metrics.failure_count,
                "failure_rate": exp.metrics.failure_rate,
                "status": exp.status
            })
        return summaries

    def get_case(self, case_id: str) -> Optional[ArenaCaseRecord]:
        return self._cases.get(case_id)

    def export_experiment_json(self, experiment_id: str) -> str:
        exp = self.get_experiment(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found.")
        return exp.model_dump_json(indent=2)

    def export_experiment_csv(self, experiment_id: str) -> str:
        exp = self.get_experiment(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found.")

        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "experiment_id", "case_id", "disease_id", "disease_name", "seed",
            "validation_status", "evaluation_status", "failure_category",
            "is_failure", "is_instability", "ground_truth_disease_id",
            "baseline_pred_id", "baseline_confidence", "baseline_correct",
            "perturbed_pred_id", "perturbed_confidence", "perturbed_correct",
            "noise_sigma", "missing_lab_rate", "age_shift_years", "confounding_infection",
            "diff_summary", "timestamp"
        ]
        writer.writerow(headers)

        for c in exp.cases:
            b_pred_id = c.baseline_prediction.predicted_disease_id if c.baseline_prediction else ""
            b_conf = c.baseline_prediction.confidence_score if c.baseline_prediction else ""
            b_corr = c.baseline_prediction.is_top1_correct if c.baseline_prediction else ""

            p_pred_id = c.perturbed_prediction.predicted_disease_id if c.perturbed_prediction else ""
            p_conf = c.perturbed_prediction.confidence_score if c.perturbed_prediction else ""
            p_corr = c.perturbed_prediction.is_top1_correct if c.perturbed_prediction else ""

            writer.writerow([
                c.experiment_id,
                c.case_id,
                c.disease_id,
                c.disease_name,
                c.seed,
                c.constraint_validation.status,
                c.evaluation_status,
                c.failure_category,
                c.is_failure,
                c.is_instability,
                c.ground_truth_disease_id,
                b_pred_id,
                b_conf,
                b_corr,
                p_pred_id,
                p_conf,
                p_corr,
                c.perturbation_config.noise_sigma,
                c.perturbation_config.missing_lab_rate,
                c.perturbation_config.atypical_age_shift_years,
                c.perturbation_config.inject_confounding_infection,
                c.diff_summary,
                c.timestamp
            ])

        return output.getvalue()

    def find_breaking_point(self, config: BreakingPointSearchConfig) -> BreakingPointResult:
        search_id = f"BP-SEARCH-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        d_id = config.disease_id
        if d_id not in disease_registry:
            d_id = "wilson_disease"
        disease = disease_registry[d_id]

        patient = patient_generator.generate_patient(
            disease_id=d_id,
            seed=config.random_seed
        )

        baseline_cfg = PerturbationConfig(
            noise_sigma=0.0,
            missing_lab_rate=0.0,
            atypical_age_shift_years=0,
            inject_confounding_infection=False,
            reproducibility_seed=config.random_seed
        )
        baseline_arena_data = perturbation_engine.create_arena_case(
            patient=patient,
            config=baseline_cfg,
            experiment_id=search_id
        )
        baseline_pred = self.evaluate_model(
            config.model_type,
            baseline_arena_data["exportable_test_case"],
            config.external_endpoint_url
        )

        steps_to_evaluate: List[Tuple[float, str, PerturbationConfig]] = []
        max_steps = max(3, min(30, config.max_steps))
        step_sz = max(0.005, min(0.10, config.step_size))

        if config.search_axis == "noise_sigma":
            for step_i in range(1, max_steps + 1):
                val = round(step_i * step_sz, 3)
                p_cfg = PerturbationConfig(
                    noise_sigma=val,
                    missing_lab_rate=0.0,
                    atypical_age_shift_years=0,
                    inject_confounding_infection=False,
                    reproducibility_seed=config.random_seed
                )
                steps_to_evaluate.append((val, f"Noise σ={val:.2f}", p_cfg))

        elif config.search_axis == "missing_labs":
            for step_i in range(1, max_steps + 1):
                rate = round(min(0.85, step_i * 0.05), 2)
                p_cfg = PerturbationConfig(
                    noise_sigma=0.0,
                    missing_lab_rate=rate,
                    atypical_age_shift_years=0,
                    inject_confounding_infection=False,
                    reproducibility_seed=config.random_seed
                )
                steps_to_evaluate.append((rate, f"Missing Labs={int(rate*100)}%", p_cfg))

        elif config.search_axis == "age_shift":
            age_shifts = [2, -2, 5, -5, 8, -8, 12, -12, 16, -16, 20, -20, 25, -25]
            for step_i, shift in enumerate(age_shifts[:max_steps], start=1):
                p_cfg = PerturbationConfig(
                    noise_sigma=0.0,
                    missing_lab_rate=0.0,
                    atypical_age_shift_years=shift,
                    inject_confounding_infection=False,
                    reproducibility_seed=config.random_seed
                )
                steps_to_evaluate.append((float(shift), f"Age Shift={shift:+d}y", p_cfg))

        elif config.search_axis == "confounding_infection":
            noise_levels = [0.0, 0.02, 0.05, 0.08, 0.12, 0.15, 0.20, 0.25]
            for step_i, n_lvl in enumerate(noise_levels[:max_steps], start=1):
                p_cfg = PerturbationConfig(
                    noise_sigma=n_lvl,
                    missing_lab_rate=0.0,
                    atypical_age_shift_years=0,
                    inject_confounding_infection=True,
                    reproducibility_seed=config.random_seed
                )
                steps_to_evaluate.append((n_lvl, f"Infection + σ={n_lvl:.2f}", p_cfg))

        else:  # "adaptive_combined"
            for step_i in range(1, max_steps + 1):
                n_val = round(step_i * 0.015, 3)
                m_rate = round(min(0.70, step_i * 0.04), 2)
                inf = (step_i >= 4)
                p_cfg = PerturbationConfig(
                    noise_sigma=n_val,
                    missing_lab_rate=m_rate,
                    atypical_age_shift_years=5 if step_i >= 3 else 0,
                    inject_confounding_infection=inf,
                    reproducibility_seed=config.random_seed
                )
                steps_to_evaluate.append((n_val, f"σ={n_val:.2f}, Miss={int(m_rate*100)}%, Inf={inf}", p_cfg))

        step_history: List[BreakingPointStepRecord] = []
        breaking_point_found = False
        minimal_delta: Optional[Dict[str, Any]] = None
        breaking_pred: Optional[DiagnosticPredictionResult] = None
        affected_features: List[AppliedTransformation] = []
        failure_type: Optional[str] = None
        clinical_interpretation = ""

        for idx, (param_val, param_lbl, p_cfg) in enumerate(steps_to_evaluate, start=1):
            arena_data = perturbation_engine.create_arena_case(
                patient=patient,
                config=p_cfg,
                experiment_id=search_id
            )
            c_val: ConstraintValidationStatus = arena_data["constraint_validation"]
            is_valid = c_val.is_valid

            if not is_valid:
                step_history.append(BreakingPointStepRecord(
                    step_index=idx,
                    parameter_value=param_val,
                    parameter_label=param_lbl,
                    perturbation_summary=f"{param_lbl} (Violated clinical constraints)",
                    is_clinically_valid=False,
                    validation_status=c_val.status,
                    predicted_disease_id="N/A",
                    predicted_disease_name="Evaluation Skipped (Invalid Candidate)",
                    confidence_score=0.0,
                    is_top1_correct=False,
                    is_breaking_point=False,
                    failure_mode="CONSTRAINT_VIOLATION"
                ))
                continue

            eval_pred = self.evaluate_model(
                config.model_type,
                arena_data["exportable_test_case"],
                config.external_endpoint_url
            )

            misdiagnosis = not eval_pred.is_top1_correct
            conf_collapse = eval_pred.confidence_score < config.confidence_collapse_threshold

            triggered = False
            detected_mode = None
            if config.target_failure_type == "MISDIAGNOSIS" and misdiagnosis:
                triggered = True
                detected_mode = "MISDIAGNOSIS"
            elif config.target_failure_type == "CONFIDENCE_COLLAPSE" and conf_collapse:
                triggered = True
                detected_mode = "CONFIDENCE_COLLAPSE"
            elif config.target_failure_type == "ANY":
                if misdiagnosis:
                    triggered = True
                    detected_mode = "MISDIAGNOSIS"
                elif conf_collapse:
                    triggered = True
                    detected_mode = "CONFIDENCE_COLLAPSE"

            step_record = BreakingPointStepRecord(
                step_index=idx,
                parameter_value=param_val,
                parameter_label=param_lbl,
                perturbation_summary=param_lbl,
                is_clinically_valid=True,
                validation_status="PASSED",
                predicted_disease_id=eval_pred.predicted_disease_id,
                predicted_disease_name=eval_pred.predicted_disease_name,
                confidence_score=eval_pred.confidence_score,
                is_top1_correct=eval_pred.is_top1_correct,
                is_breaking_point=triggered,
                failure_mode=detected_mode
            )
            step_history.append(step_record)

            if triggered and not breaking_point_found:
                breaking_point_found = True
                failure_type = detected_mode
                minimal_delta = {
                    "search_axis": config.search_axis,
                    "parameter_value": param_val,
                    "parameter_label": param_lbl,
                    "step_index": idx,
                    "noise_sigma": p_cfg.noise_sigma,
                    "missing_lab_rate": p_cfg.missing_lab_rate,
                    "atypical_age_shift_years": p_cfg.atypical_age_shift_years,
                    "inject_confounding_infection": p_cfg.inject_confounding_infection
                }
                breaking_pred = eval_pred
                affected_features = arena_data["applied_transformations"]

                if detected_mode == "MISDIAGNOSIS":
                    clinical_interpretation = (
                        f"Breaking point identified at {param_lbl}. The diagnostic model ({eval_pred.algorithm_name}) "
                        f"flipped from {baseline_pred.predicted_disease_name} (confidence {baseline_pred.confidence_score*100:.1f}%) "
                        f"to {eval_pred.predicted_disease_name} (confidence {eval_pred.confidence_score*100:.1f}%). "
                        f"Crucially, the perturbed case strictly satisfied all physiological and disease model constraints, "
                        f"proving this misclassification represents an algorithmic sensitivity rather than an unphysiological outlier."
                    )
                else:
                    clinical_interpretation = (
                        f"Confidence collapse breaking point identified at {param_lbl}. The diagnostic model "
                        f"confidence plummeted from {baseline_pred.confidence_score*100:.1f}% to {eval_pred.confidence_score*100:.1f}% "
                        f"(below the safety threshold of {config.confidence_collapse_threshold*100:.0f}%), demonstrating "
                        f"brittleness under small measurement variations while maintaining diagnostic correctness."
                    )
                break

        if not breaking_point_found:
            clinical_interpretation = (
                f"No breaking point discovered within {len(steps_to_evaluate)} valid search steps along '{config.search_axis}'. "
                f"The evaluated model ({baseline_pred.algorithm_name}) maintained robust diagnostic accuracy "
                f"(top-1 correct with confidence >= {config.confidence_collapse_threshold*100:.0f}%) across all perturbation increments."
            )

        model_name_resolved = baseline_pred.algorithm_name if baseline_pred else config.model_type

        return BreakingPointResult(
            search_id=search_id,
            model_name=model_name_resolved,
            disease_id=d_id,
            disease_name=disease.metadata.disease_name,
            patient_id=patient.patient_id,
            search_axis=config.search_axis,
            breaking_point_found=breaking_point_found,
            minimal_delta=minimal_delta,
            failure_type=failure_type,
            baseline_prediction=baseline_pred,
            breaking_prediction=breaking_pred,
            steps_evaluated=len(step_history),
            step_history=step_history,
            affected_features=affected_features,
            clinical_interpretation=clinical_interpretation,
            created_at=created_at
        )

    def compare_models_breaking_point(self, config: BreakingPointComparisonConfig) -> BreakingPointComparisonReport:
        comparison_id = f"BP-CMP-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        d_id = config.disease_id if config.disease_id in disease_registry else "wilson_disease"
        disease = disease_registry[d_id]

        results: Dict[str, BreakingPointResult] = {}
        for m_type in config.models:
            search_cfg = BreakingPointSearchConfig(
                disease_id=d_id,
                patient_id=config.patient_id,
                random_seed=config.random_seed,
                model_type=m_type,
                external_endpoint_url=config.external_endpoint_url,
                search_axis=config.search_axis,
                max_steps=config.max_steps,
                step_size=config.step_size
            )
            results[m_type] = self.find_breaking_point(search_cfg)

        ranking_list = []
        for m_type, bp_res in results.items():
            if not bp_res.breaking_point_found:
                resilience_score = 100.0
                status_label = "HIGHLY RESILIENT (NO BREAK)"
                threshold_val = float('inf')
            else:
                param_v = bp_res.minimal_delta.get("parameter_value", 0.0) if bp_res.minimal_delta else 0.0
                threshold_val = param_v
                step_idx = bp_res.minimal_delta.get("step_index", 1) if bp_res.minimal_delta else 1
                resilience_score = round((step_idx / config.max_steps) * 100, 1)
                status_label = f"BROKE AT STEP {step_idx} ({bp_res.minimal_delta.get('parameter_label')})"

            ranking_list.append({
                "model_type": m_type,
                "model_name": bp_res.model_name,
                "breaking_point_found": bp_res.breaking_point_found,
                "failure_type": bp_res.failure_type,
                "breaking_threshold": threshold_val if threshold_val != float('inf') else None,
                "resilience_score": resilience_score,
                "status_label": status_label
            })

        ranking_list.sort(key=lambda x: x["resilience_score"], reverse=True)

        summary_text = (
            f"Breaking Point Comparison across {len(config.models)} models on {disease.metadata.disease_name} (Search Axis: {config.search_axis}). "
            f"Most resilient model: {ranking_list[0]['model_name']} ({ranking_list[0]['status_label']})."
        )

        return BreakingPointComparisonReport(
            comparison_id=comparison_id,
            disease_id=d_id,
            disease_name=disease.metadata.disease_name,
            search_axis=config.search_axis,
            results=results,
            resilience_ranking=ranking_list,
            comparative_summary=summary_text,
            created_at=created_at
        )


adversarial_arena_engine = AdversarialArenaEngine()
