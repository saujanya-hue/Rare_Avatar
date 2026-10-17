"""Synthetic Patient Population Lab Generator.

Generates batch cohorts of rare-disease synthetic patient avatars,
runs automated 5-category Consistency Guardian audits, calculates population-level
distributions, and provides multi-format exports and Arena benchmark bridges.
"""
import uuid
import datetime
import io
import csv
import json
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.population import (
    PopulationCohortConfig, PopulationDemographicsSummary,
    PopulationValidationSummary, PopulationMemberRecord,
    PopulationCohortRecord
)
from app.schemas.diagnostic import ArenaExperimentConfig, ArenaExperimentResult
from app.generators.patient_generator import patient_generator
from app.validation.consistency_checker import consistency_checker
from app.disease_models import disease_registry


class PopulationGenerator:
    def __init__(self):
        # Maps cohort_id -> (PopulationCohortRecord, List[SyntheticPatientSpecification])
        self._cohorts: Dict[str, Tuple[PopulationCohortRecord, List[SyntheticPatientSpecification]]] = {}

    def generate_cohort(self, config: PopulationCohortConfig) -> PopulationCohortRecord:
        cohort_id = f"COHORT-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        patients: List[SyntheticPatientSpecification] = []
        members: List[PopulationMemberRecord] = []

        base_seed = config.base_seed
        case_idx = 0

        # Category violation counters
        violations_by_cat: Dict[str, int] = {
            "PHYSIOLOGICAL": 0,
            "CROSS_MODAL": 0,
            "TEMPORAL": 0,
            "TREATMENT_MODEL": 0,
            "EVIDENCE_GROUNDING": 0
        }
        passed_count = 0
        warning_count = 0
        failed_count = 0

        for d_id, count in config.disease_distribution.items():
            if d_id not in disease_registry:
                continue

            for _ in range(max(1, count)):
                case_idx += 1
                case_seed = base_seed + (case_idx * 137)

                pt = patient_generator.generate_patient(disease_id=d_id, seed=case_seed)
                patients.append(pt)

                # Run Consistency Guardian validation
                v_results = consistency_checker.validate_patient(pt)
                fatal = [r for r in v_results if not r.passed and r.severity == "FATAL_ERROR"]
                warns = [r for r in v_results if r.status == "WARNING" or r.severity == "WARNING"]

                for r in fatal:
                    cat = r.category
                    violations_by_cat[cat] = violations_by_cat.get(cat, 0) + 1

                if fatal:
                    v_status = "FAILED"
                    failed_count += 1
                elif warns:
                    v_status = "WARNING"
                    warning_count += 1
                else:
                    v_status = "PASSED"
                    passed_count += 1

                # Extract primary biomarker
                marker_name, marker_val, marker_unit = self._get_primary_biomarker(pt)

                members.append(PopulationMemberRecord(
                    patient_id=pt.patient_id,
                    disease_id=pt.disease.disease_id,
                    disease_name=pt.disease.disease_name,
                    age_years=pt.demographics.age_years,
                    biological_sex=pt.demographics.biological_sex,
                    stage=pt.baseline_disease_stage,
                    primary_biomarker_name=marker_name,
                    primary_biomarker_value=marker_val,
                    unit=marker_unit,
                    validation_status=v_status,
                    seed=case_seed
                ))

        # Demographic summary statistics
        ages = [m.age_years for m in members]
        sex_dist: Dict[str, int] = {}
        stage_dist: Dict[str, int] = {}
        disease_counts: Dict[str, int] = {}

        for m in members:
            sex_dist[m.biological_sex] = sex_dist.get(m.biological_sex, 0) + 1
            stage_dist[m.stage] = stage_dist.get(m.stage, 0) + 1
            disease_counts[m.disease_id] = disease_counts.get(m.disease_id, 0) + 1

        demo_summary = PopulationDemographicsSummary(
            total_patients=len(members),
            age_mean=round(float(np.mean(ages)), 1) if ages else 0.0,
            age_std=round(float(np.std(ages)), 1) if ages else 0.0,
            age_min=int(min(ages)) if ages else 0,
            age_max=int(max(ages)) if ages else 0,
            sex_distribution=sex_dist,
            stage_distribution=stage_dist,
            disease_counts=disease_counts
        )

        total_cases = len(members)
        pass_rate = round(((passed_count + warning_count) / max(1, total_cases)) * 100, 1)

        val_summary = PopulationValidationSummary(
            total_cases_validated=total_cases,
            pass_rate=pass_rate,
            passed_count=passed_count,
            warning_count=warning_count,
            failed_count=failed_count,
            violations_by_category=violations_by_cat
        )

        record = PopulationCohortRecord(
            cohort_id=cohort_id,
            cohort_name=config.cohort_name,
            created_at=created_at,
            config=config,
            demographics_summary=demo_summary,
            validation_summary=val_summary,
            roster=members
        )

        self._cohorts[cohort_id] = (record, patients)
        return record

    def get_cohort(self, cohort_id: str) -> Optional[PopulationCohortRecord]:
        if cohort_id in self._cohorts:
            return self._cohorts[cohort_id][0]
        return None

    def list_cohorts(self) -> List[PopulationCohortRecord]:
        return [c[0] for c in self._cohorts.values()]

    def export_cohort_csv(self, cohort_id: str) -> str:
        if cohort_id not in self._cohorts:
            raise ValueError(f"Cohort '{cohort_id}' not found.")

        record, _ = self._cohorts[cohort_id]
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "cohort_id", "cohort_name", "patient_id", "disease_id", "disease_name",
            "age_years", "biological_sex", "stage", "primary_biomarker_name",
            "primary_biomarker_value", "unit", "validation_status", "seed"
        ])

        for m in record.roster:
            writer.writerow([
                record.cohort_id,
                record.cohort_name,
                m.patient_id,
                m.disease_id,
                m.disease_name,
                m.age_years,
                m.biological_sex,
                m.stage,
                m.primary_biomarker_name,
                m.primary_biomarker_value,
                m.unit,
                m.validation_status,
                m.seed
            ])

        return output.getvalue()

    def export_cohort_json(self, cohort_id: str) -> str:
        if cohort_id not in self._cohorts:
            raise ValueError(f"Cohort '{cohort_id}' not found.")
        record, _ = self._cohorts[cohort_id]
        return record.model_dump_json(indent=2)

    def _get_primary_biomarker(self, pt: SyntheticPatientSpecification) -> Tuple[str, float, str]:
        lab_dict = {l.test_code: l for l in pt.lab_history}
        d_id = pt.disease.disease_id

        if d_id == "wilson_disease":
            lab = lab_dict.get("URINARY_COPPER_24H")
            if lab:
                return ("24h Urinary Copper", float(lab.value), lab.unit)
            return ("Serum Ceruloplasmin", 8.5, "mg/dL")

        elif d_id == "fabry_disease":
            lab = lab_dict.get("LYSO_GB3")
            if lab:
                return ("Plasma Lyso-Gb3", float(lab.value), lab.unit)
            return ("Plasma Lyso-Gb3", 28.0, "ng/mL")

        else:  # Gaucher
            lab = lab_dict.get("PLATELETS")
            if lab:
                return ("Platelet Count", float(lab.value), lab.unit)
            return ("Plasma Lyso-Gb1", 145.0, "ng/mL")


population_generator = PopulationGenerator()
