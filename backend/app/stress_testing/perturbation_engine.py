"""Controlled Perturbation Engine for Diagnostic Algorithm Stress-Testing."""
import copy
import uuid
import numpy as np
from typing import Dict, Any, List
from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.diagnostic import PerturbationConfig, ExportableTestCase


from typing import Dict, Any, List, Tuple, Optional
from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.diagnostic import (
    PerturbationConfig, ExportableTestCase, AppliedTransformation,
    ConstraintValidationStatus, ArenaCaseRecord
)
from app.disease_models import disease_registry
from app.validation.consistency_checker import consistency_checker


class PerturbationEngine:
    def create_perturbed_test_case(
        self, patient: SyntheticPatientSpecification, config: PerturbationConfig
    ) -> ExportableTestCase:
        arena_res = self.create_arena_case(patient, config, experiment_id="EXP-LEGACY", id_prefix="TC-STRESS-")
        return arena_res["exportable_test_case"]

    def create_arena_case(
        self,
        patient: SyntheticPatientSpecification,
        config: PerturbationConfig,
        experiment_id: str = "EXP-DEFAULT",
        id_prefix: str = "ARENA-"
    ) -> Dict[str, Any]:
        rng = np.random.default_rng(config.reproducibility_seed)
        test_case_id = f"{id_prefix}{patient.disease.disease_id[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

        applied_transformations: List[AppliedTransformation] = []
        violations: List[str] = []
        warnings: List[str] = []
        details: List[Dict[str, Any]] = []

        # 0. Capture Original Inputs (Blinded format for comparison)
        original_inputs = {
            "demographics": {
                "age_years": patient.demographics.age_years,
                "biological_sex": patient.demographics.biological_sex,
                "ethnicity": patient.demographics.ethnicity
            },
            "symptoms": [
                {
                    "symptom_name": s.name,
                    "category": s.category,
                    "onset_month": s.onset_month,
                    "severity_score": s.severity_score
                }
                for s in patient.symptoms
            ],
            "laboratory": [
                {
                    "test_code": l.test_code,
                    "test_name": l.test_name,
                    "value": l.value,
                    "unit": l.unit,
                    "ref_low": l.ref_low,
                    "ref_high": l.ref_high
                }
                for l in patient.lab_history
            ],
            "imaging_summary": [
                {
                    "modality": img.modality,
                    "anatomical_region": img.anatomical_region,
                    "findings": img.acr_findings,
                    "pathological_signs": img.pathological_signs
                }
                for img in patient.imaging_studies
            ]
        }

        # 1. Blinded Demographics (apply age shift if configured)
        orig_age = patient.demographics.age_years
        shifted_age = orig_age
        if config.atypical_age_shift_years != 0:
            shifted_age = max(8, min(85, orig_age + config.atypical_age_shift_years))
            applied_transformations.append(AppliedTransformation(
                transformation_type="ATYPICAL_AGE_SHIFT",
                feature_name="Demographics: Age",
                original_value=orig_age,
                perturbed_value=shifted_age,
                delta=f"{config.atypical_age_shift_years:+d} yrs",
                unit="years",
                reason=f"Shifted age from {orig_age} to {shifted_age} to test algorithmic sensitivity to atypical presentation age."
            ))

        blinded_demographics = {
            "age_years": shifted_age,
            "biological_sex": patient.demographics.biological_sex,
            "ethnicity": patient.demographics.ethnicity
        }

        # 2. Symptoms with optional noise
        blinded_symptoms = []
        for sym in patient.symptoms:
            orig_sev = sym.severity_score
            if config.noise_sigma > 0:
                noise_delta = float(rng.normal(0, config.noise_sigma * 2.0))
                perturbed_sev = float(np.round(np.clip(orig_sev + noise_delta, 0.0, 10.0), 1))
                if abs(perturbed_sev - orig_sev) >= 0.2:
                    applied_transformations.append(AppliedTransformation(
                        transformation_type="MEASUREMENT_NOISE",
                        feature_name=f"Symptom: {sym.name}",
                        original_value=orig_sev,
                        perturbed_value=perturbed_sev,
                        delta=f"{perturbed_sev - orig_sev:+.1f}",
                        unit="score (0-10)",
                        reason=f"Subjective clinical reporting noise at sigma={config.noise_sigma}"
                    ))
            else:
                perturbed_sev = orig_sev

            blinded_symptoms.append({
                "symptom_name": sym.name,
                "category": sym.category,
                "onset_month": sym.onset_month,
                "severity_score": perturbed_sev
            })

        # 3. Laboratory with Controlled Measurement Noise and Missing Test Rates
        blinded_labs = []
        withheld_codes = []
        for lab in patient.lab_history:
            # Check missing rate dropout
            if config.missing_lab_rate > 0 and rng.uniform() < config.missing_lab_rate:
                withheld_codes.append(lab.test_code)
                applied_transformations.append(AppliedTransformation(
                    transformation_type="MISSING_LAB_DROPOUT",
                    feature_name=f"Lab: {lab.test_name} ({lab.test_code})",
                    original_value=f"{lab.value} {lab.unit}",
                    perturbed_value="WITHHELD / MISSING",
                    delta="REMOVED",
                    unit=lab.unit,
                    reason=f"Withheld laboratory measurement to simulate incomplete diagnostic workup."
                ))
                continue

            # Apply Gaussian measurement noise
            orig_val = lab.value
            if config.noise_sigma > 0:
                relative_noise = float(rng.normal(0, config.noise_sigma))
                noisy_val = float(np.round(max(0.01, orig_val * (1.0 + relative_noise)), 2))
                delta_num = round(noisy_val - orig_val, 2)
                applied_transformations.append(AppliedTransformation(
                    transformation_type="MEASUREMENT_NOISE",
                    feature_name=f"Lab: {lab.test_name} ({lab.test_code})",
                    original_value=orig_val,
                    perturbed_value=noisy_val,
                    delta=f"{delta_num:+0.2f}",
                    unit=lab.unit,
                    reason=f"Gaussian measurement noise (sigma={config.noise_sigma})"
                ))
            else:
                noisy_val = orig_val

            blinded_labs.append({
                "test_code": lab.test_code,
                "test_name": lab.test_name,
                "value": noisy_val,
                "unit": lab.unit,
                "ref_low": lab.ref_low,
                "ref_high": lab.ref_high
            })

        # 4. Inject confounding intercurrent infection if configured
        if config.inject_confounding_infection:
            crp_val = float(np.round(rng.uniform(45.0, 110.0), 1))
            wbc_val = float(np.round(rng.uniform(14.5, 19.8), 1))
            blinded_labs.append({
                "test_code": "CRP",
                "test_name": "C-Reactive Protein (Confounder)",
                "value": crp_val,
                "unit": "mg/L",
                "ref_low": 0.0,
                "ref_high": 5.0
            })
            applied_transformations.append(AppliedTransformation(
                transformation_type="CONFOUNDING_INFECTION",
                feature_name="Lab: C-Reactive Protein (Confounder)",
                original_value="Normal / Not reported",
                perturbed_value=f"{crp_val} mg/L",
                delta=f"+{crp_val}",
                unit="mg/L",
                reason="Injected acute systemic inflammatory response confounder."
            ))
            blinded_labs.append({
                "test_code": "WBC",
                "test_name": "White Blood Cell Count (Confounder)",
                "value": wbc_val,
                "unit": "x10^3/uL",
                "ref_low": 4.5,
                "ref_high": 11.0
            })
            applied_transformations.append(AppliedTransformation(
                transformation_type="CONFOUNDING_INFECTION",
                feature_name="Lab: White Blood Cell Count (Confounder)",
                original_value="Normal / Not reported",
                perturbed_value=f"{wbc_val} x10^3/uL",
                delta=f"+{wbc_val}",
                unit="x10^3/uL",
                reason="Injected leukocytosis confounding infection profile."
            ))

        # 5. Imaging Summary (Blinded of definitive diagnosis name)
        blinded_imaging = []
        for img in patient.imaging_studies:
            blinded_imaging.append({
                "modality": img.modality,
                "anatomical_region": img.anatomical_region,
                "findings": img.acr_findings,
                "pathological_signs": img.pathological_signs,
                "parametric_features": [f.model_dump() for f in img.parametric_features]
            })

        # 6. Constraint and Plausibility Validation
        disease_model = disease_registry.get_model(patient.disease.disease_id)
        lab_dict = {l["test_code"]: l["value"] for l in blinded_labs}

        # Check hard physiological constraints from disease model
        if disease_model:
            for rule in disease_model.get_physiological_constraints():
                if rule.get("category") == "Physiological Range":
                    code = rule.get("test_code")
                    if code in lab_dict:
                        v = lab_dict[code]
                        severity = rule.get("severity", "FATAL_ERROR")
                        rule_passed = True
                        if "max_value" in rule and v > rule["max_value"]:
                            rule_passed = False
                        if "min_value" in rule and v < rule["min_value"]:
                            rule_passed = False

                        check_info = {
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "test_code": code,
                            "observed_value": v,
                            "passed": rule_passed,
                            "severity": severity,
                            "description": rule.get("description")
                        }
                        details.append(check_info)

                        if not rule_passed:
                            msg = f"{rule.get('name')}: {code} value {v} violates constraint ({rule.get('description')})"
                            if severity == "FATAL_ERROR":
                                violations.append(msg)
                            else:
                                warnings.append(msg)

        # Check sufficiency of diagnostic reference information
        d_id = patient.disease.disease_id
        insufficient_evidence = False
        if d_id == "wilson_disease":
            has_cu = "URINARY_COPPER_24H" in lab_dict
            has_cp = "CERULOPLASMIN" in lab_dict
            has_kf = any(any("Kayser" in s for s in img.get("pathological_signs", [])) for img in blinded_imaging)
            if not has_cu and not has_cp and not has_kf:
                insufficient_evidence = True
                warnings.append("Insufficient Wilson disease diagnostic markers: ceruloplasmin, 24h copper, and KF ring all absent.")
        elif d_id == "fabry_disease":
            has_gb3 = "LYSO_GB3" in lab_dict
            has_agal = "ALPHA_GALACTOSIDASE_A" in lab_dict
            if not has_gb3 and not has_agal:
                insufficient_evidence = True
                warnings.append("Insufficient Fabry disease diagnostic markers: both Lyso-Gb3 and Alpha-Galactosidase absent.")
        elif d_id == "gaucher_disease":
            has_gb1 = "LYSO_GB1" in lab_dict
            has_bglu = "BETA_GLUCOSIDASE" in lab_dict
            if not has_gb1 and not has_bglu:
                insufficient_evidence = True
                warnings.append("Insufficient Gaucher disease diagnostic markers: both Lyso-Gb1 and Beta-Glucosidase absent.")

        is_valid = len(violations) == 0
        status_str = "PASSED" if is_valid else "VIOLATED"
        if is_valid and len(warnings) > 0:
            status_str = "WARNING"

        constraint_status = ConstraintValidationStatus(
            is_valid=is_valid,
            status=status_str,
            violations=violations,
            warnings=warnings,
            details=details
        )

        # Build human-readable Diff Summary
        diff_parts = []
        if shifted_age != orig_age:
            diff_parts.append(f"Age {orig_age} -> {shifted_age} ({config.atypical_age_shift_years:+d}y)")
        if withheld_codes:
            diff_parts.append(f"{len(withheld_codes)} labs withheld ({', '.join(withheld_codes[:3])}{'...' if len(withheld_codes) > 3 else ''})")
        if config.noise_sigma > 0:
            diff_parts.append(f"Noise σ={config.noise_sigma}")
        if config.inject_confounding_infection:
            diff_parts.append("Infection confounder (CRP+WBC)")
        if not diff_parts:
            diff_parts.append("No perturbations (Baseline unperturbed)")
        diff_summary = "; ".join(diff_parts)

        blinded_inputs = {
            "demographics": blinded_demographics,
            "symptoms": blinded_symptoms,
            "laboratory": blinded_labs,
            "imaging_summary": blinded_imaging
        }

        exportable_tc = ExportableTestCase(
            test_case_id=test_case_id,
            patient_id=patient.patient_id,
            reproducibility_seed=config.reproducibility_seed,
            perturbation_applied=config,
            input_demographics=blinded_demographics,
            input_symptoms=blinded_symptoms,
            input_laboratory=blinded_labs,
            input_imaging_summary=blinded_imaging,
            ground_truth_disease_id=patient.disease.disease_id,
            ground_truth_disease_name=patient.disease.disease_name,
            ground_truth_omim=patient.disease.omim_id,
            ground_truth_stage=patient.baseline_disease_stage
        )

        return {
            "test_case_id": test_case_id,
            "blinded_inputs": blinded_inputs,
            "original_inputs": original_inputs,
            "applied_transformations": applied_transformations,
            "constraint_validation": constraint_status,
            "insufficient_evidence": insufficient_evidence,
            "diff_summary": diff_summary,
            "exportable_test_case": exportable_tc
        }


perturbation_engine = PerturbationEngine()

