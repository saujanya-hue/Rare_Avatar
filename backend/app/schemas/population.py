"""Schemas for Synthetic Patient Population Lab."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class PopulationCohortConfig(BaseModel):
    cohort_name: str = "Rare-Disease Benchmark Cohort"
    disease_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "wilson_disease": 4,
            "fabry_disease": 4,
            "gaucher_disease": 4
        }
    )
    base_seed: int = 42
    notes: Optional[str] = None


class PopulationDemographicsSummary(BaseModel):
    total_patients: int
    age_mean: float
    age_std: float
    age_min: int
    age_max: int
    sex_distribution: Dict[str, int]
    stage_distribution: Dict[str, int]
    disease_counts: Dict[str, int]


class PopulationValidationSummary(BaseModel):
    total_cases_validated: int
    pass_rate: float
    passed_count: int
    warning_count: int
    failed_count: int
    violations_by_category: Dict[str, int] = Field(default_factory=dict)


class PopulationMemberRecord(BaseModel):
    patient_id: str
    disease_id: str
    disease_name: str
    age_years: int
    biological_sex: str
    stage: str
    primary_biomarker_name: str
    primary_biomarker_value: float
    unit: str
    validation_status: str  # "PASSED", "WARNING", "FAILED"
    seed: int


class PopulationCohortRecord(BaseModel):
    cohort_id: str
    cohort_name: str
    created_at: str
    config: PopulationCohortConfig
    demographics_summary: PopulationDemographicsSummary
    validation_summary: PopulationValidationSummary
    roster: List[PopulationMemberRecord] = Field(default_factory=list)
