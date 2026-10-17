from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class Demographics(BaseModel):
    synthetic_id: str
    age_years: int
    biological_sex: str
    ethnicity: str
    synthetic_seed: int
    is_pediatric: bool = False


class DiseaseMetadata(BaseModel):
    disease_id: str
    disease_name: str
    omim_id: str
    orpha_code: str
    genetic_basis: str
    prevalence: str
    inheritance: str


class EvidenceReference(BaseModel):
    evidence_id: str
    pmid: Optional[str] = None
    title: str
    authors: str
    journal: str
    year: int
    evidence_level: str  # e.g., "Level A (Systematic Review)", "Level B (Cohort)", "Level C (Case Series)"
    doi: Optional[str] = None
    url: Optional[str] = None
    relevance_summary: str


class UncertaintyBounds(BaseModel):
    point_estimate: float
    ci_95_low: float
    ci_95_high: float
    aleatoric_variance: float
    epistemic_confidence_score: float  # 0.0 to 1.0 based on evidence density
    uncertainty_source: str
    methodology: str = "Empirical Natural-History Variance & Conformal Interval"


class ClinicalSymptom(BaseModel):
    symptom_id: str
    name: str
    category: str  # Hepatic, Neurologic, Ophthalmic, Renal, Dermatologic, etc.
    onset_month: int
    severity_score: float  # 0.0 to 10.0
    description: str
    is_revealed: bool = False
    evidence_ids: List[str] = []


class LabMeasurement(BaseModel):
    measurement_id: str
    test_code: str
    test_name: str
    category: str
    value: float
    unit: str
    ref_low: float
    ref_high: float
    is_abnormal: bool
    timestamp_month: int
    uncertainty: UncertaintyBounds
    evidence_ids: List[str] = []
    ordered: bool = False
    reported: bool = False


class ImagingParametricFeature(BaseModel):
    feature_name: str
    z_score: float
    quantitative_value: Optional[float] = None
    unit: Optional[str] = None
    attenuation_or_signal: Optional[str] = None
    organ: str


class ImagingStudy(BaseModel):
    study_id: str
    modality: str  # e.g. "MRI Brain", "Abdominal Ultrasound", "Renal Ultrasound", "Skeletal Radiograph"
    anatomical_region: str
    timestamp_month: int
    acronym: str
    acr_findings: str
    radiology_impression: str
    parametric_features: List[ImagingParametricFeature]
    pathological_signs: List[str]  # e.g., ["Face of Giant Panda", "Kayser-Fleischer Rings", "Erlenmeyer Flask Deformity"]
    evidence_ids: List[str] = []
    ordered: bool = False
    reported: bool = False
    schematic_data: Dict[str, Any] = {}  # Normalized coordinates/geometry for calibrated visual slice rendering


class ClinicalEncounterNote(BaseModel):
    encounter_id: str
    timestamp_month: int
    encounter_type: str  # "Initial Presentation", "Follow-up", "Acute Exacerbation"
    chief_complaint: str
    hpi: str
    physical_exam: Dict[str, str]
    assessment_and_plan: str
    disease_stage: str


class CounterfactualTrajectoryPoint(BaseModel):
    month: int
    state_score: float  # 0.0 (asymptomatic/controlled) to 1.0 (severe/end-stage)
    primary_biomarker_value: float
    clinical_status: str
    ci_low: float
    ci_high: float


class TreatmentResponseScenario(BaseModel):
    scenario_id: str
    name: str
    intervention_type: str  # "Targeted Therapy", "Delayed Treatment", "Standard Care", "Untreated Natural History"
    description: str
    evidence_ids: List[str] = []
    trajectory: List[CounterfactualTrajectoryPoint]
    is_active: bool = False


class SyntheticPatientSpecification(BaseModel):
    patient_id: str
    demographics: Demographics
    disease: DiseaseMetadata
    baseline_disease_stage: str
    current_simulation_month: int
    symptoms: List[ClinicalSymptom]
    lab_history: List[LabMeasurement]
    imaging_studies: List[ImagingStudy]
    clinical_notes: List[ClinicalEncounterNote]
    treatment_scenarios: List[TreatmentResponseScenario]
    active_treatment: Optional[str] = None
    evidence_catalog: Dict[str, EvidenceReference]
    created_at_utc: str
    reproducibility_seed: int


class TraineeSafePatientView(BaseModel):
    """View provided to clinical trainees - hides ground truth diagnosis, unrevealed symptoms and un-ordered tests."""
    patient_id: str
    age_years: int
    biological_sex: str
    ethnicity: str
    current_simulation_month: int
    chief_complaint: str
    active_symptoms_revealed: List[ClinicalSymptom]
    available_labs: List[LabMeasurement]
    available_imaging: List[ImagingStudy]
    available_notes: List[ClinicalEncounterNote]
    active_treatment: Optional[str] = None
    available_test_catalog: List[Dict[str, str]]
    simulation_status: str
