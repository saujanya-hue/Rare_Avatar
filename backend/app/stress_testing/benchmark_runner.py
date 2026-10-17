"""Evaluation runner and reference diagnostic classifier for stress-testing."""
from typing import Dict, Any, List, Optional
from app.schemas.diagnostic import ExportableTestCase, AlgorithmSubmission, StressTestEvaluationResult


class ReferenceDiagnosticClassifier:
    """
    Built-in reference rule-based / Bayesian clinical diagnostic model
    derived from EASL, Ortiz et al., and Pastores et al. guidelines.
    Used as an evaluation baseline or when no external API is plugged in.
    """
    def predict(self, test_case: ExportableTestCase) -> AlgorithmSubmission:
        scores: Dict[str, float] = {
            "wilson_disease": 0.05,
            "fabry_disease": 0.05,
            "gaucher_disease": 0.05,
            "other_idiopathic": 0.10
        }

        lab_dict = {l["test_code"]: l["value"] for l in test_case.input_laboratory}

        # 1. Wilson Disease Evidence (Leipzig Score heuristic)
        if "CERULOPLASMIN" in lab_dict:
            if lab_dict["CERULOPLASMIN"] < 10.0:
                scores["wilson_disease"] += 0.45
            elif lab_dict["CERULOPLASMIN"] < 20.0:
                scores["wilson_disease"] += 0.25

        if "URINARY_COPPER_24H" in lab_dict:
            if lab_dict["URINARY_COPPER_24H"] > 100.0:
                scores["wilson_disease"] += 0.40

        for img in test_case.input_imaging_summary:
            if any("Panda" in s or "Putaminal" in s or "Kayser" in s for s in img.get("pathological_signs", [])):
                scores["wilson_disease"] += 0.50

        # 2. Fabry Disease Evidence
        if "LYSO_GB3" in lab_dict:
            if lab_dict["LYSO_GB3"] > 10.0:
                scores["fabry_disease"] += 0.60
        if "ALPHA_GALACTOSIDASE_A" in lab_dict:
            if lab_dict["ALPHA_GALACTOSIDASE_A"] < 2.0:
                scores["fabry_disease"] += 0.50

        for img in test_case.input_imaging_summary:
            if any("T1 Mapping" in s or "LGE" in s or "Gadolinium" in s for s in img.get("pathological_signs", [])):
                scores["fabry_disease"] += 0.35

        # 3. Gaucher Disease Evidence
        if "LYSO_GB1" in lab_dict:
            if lab_dict["LYSO_GB1"] > 10.0:
                scores["gaucher_disease"] += 0.60
        if "BETA_GLUCOSIDASE" in lab_dict:
            if lab_dict["BETA_GLUCOSIDASE"] < 2.0:
                scores["gaucher_disease"] += 0.50
        if "PLATELETS" in lab_dict and lab_dict["PLATELETS"] < 100.0:
            scores["gaucher_disease"] += 0.20

        for img in test_case.input_imaging_summary:
            if any("Erlenmeyer" in s or "Splenomegaly" in s for s in img.get("pathological_signs", [])):
                scores["gaucher_disease"] += 0.40

        # Normalize probabilities with softmax-like scaling
        total = sum(scores.values())
        norm_scores = {k: round(v / total, 3) for k, v in scores.items()}

        sorted_preds = sorted(norm_scores.items(), key=lambda item: item[1], reverse=True)
        top1_disease_id, top1_prob = sorted_preds[0]

        name_map = {
            "wilson_disease": "Wilson Disease",
            "fabry_disease": "Fabry Disease",
            "gaucher_disease": "Gaucher Disease Type 1",
            "other_idiopathic": "Idiopathic / Non-Rare Condition"
        }

        differential = [{name_map.get(k, k): v} for k, v in sorted_preds]

        return AlgorithmSubmission(
            test_case_id=test_case.test_case_id,
            predicted_disease_id=top1_disease_id,
            predicted_disease_name=name_map.get(top1_disease_id, top1_disease_id),
            confidence_score=top1_prob,
            differential_diagnoses=differential,
            reasoning=f"Automated clinical decision algorithm evaluating {len(test_case.input_laboratory)} reported labs and {len(test_case.input_imaging_summary)} imaging studies.",
            algorithm_name="Reference Guideline Classifier (Baseline)"
        )


class BenchmarkRunner:
    def __init__(self):
        self.ref_classifier = ReferenceDiagnosticClassifier()
        self._test_cases: Dict[str, ExportableTestCase] = {}
        self._results_history: List[StressTestEvaluationResult] = []

    def store_test_case(self, tc: ExportableTestCase) -> None:
        self._test_cases[tc.test_case_id] = tc

    def get_test_case(self, test_case_id: str) -> Optional[ExportableTestCase]:
        return self._test_cases.get(test_case_id)

    def evaluate_submission(
        self, submission: AlgorithmSubmission
    ) -> StressTestEvaluationResult:
        tc = self.get_test_case(submission.test_case_id)
        if not tc:
            raise ValueError(f"Test case {submission.test_case_id} not found in benchmark registry.")

        is_top1 = (submission.predicted_disease_id == tc.ground_truth_disease_id)

        # Check top 3
        top3_ids = [list(d.keys())[0] for d in submission.differential_diagnoses[:3]]
        # Match either exact ID or disease name
        is_top3 = is_top1 or any(
            tc.ground_truth_disease_id in name.lower() or tc.ground_truth_disease_name.lower() in name.lower()
            for name in top3_ids
        )

        # Brier score contribution: (predicted_prob_of_true - 1)^2
        true_prob = 0.0
        for d in submission.differential_diagnoses:
            for k, prob in d.items():
                if tc.ground_truth_disease_id in k.lower() or tc.ground_truth_disease_name.lower() in k.lower():
                    true_prob = prob
                    break

        brier = round((true_prob - 1.0) ** 2, 4)

        # Robustness penalty based on perturbation configuration
        p_cfg = tc.perturbation_applied
        penalty = (p_cfg.noise_sigma * 1.5) + (p_cfg.missing_lab_rate * 0.8) + (0.2 if p_cfg.inject_confounding_infection else 0.0)
        base_robustness = 1.0 if is_top1 else 0.3
        robustness = max(0.1, round(base_robustness * (1.0 - min(0.6, penalty)), 2))

        summary = (
            f"Noise σ={p_cfg.noise_sigma}, Missing Lab Rate={int(p_cfg.missing_lab_rate*100)}%, "
            f"Infection Confounder={'Yes' if p_cfg.inject_confounding_infection else 'No'}"
        )

        res = StressTestEvaluationResult(
            test_case_id=tc.test_case_id,
            algorithm_name=submission.algorithm_name,
            is_top1_correct=is_top1,
            is_top3_correct=is_top3,
            ground_truth=tc.ground_truth_disease_name,
            prediction=submission.predicted_disease_name,
            confidence=submission.confidence_score,
            brier_score_contribution=brier,
            perturbation_summary=summary,
            robustness_score=robustness
        )

        self._results_history.append(res)
        return res

    def get_evaluation_history(self) -> List[StressTestEvaluationResult]:
        return self._results_history


benchmark_runner = BenchmarkRunner()
