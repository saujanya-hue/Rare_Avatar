"""Schemas for Medical Evidence Explorer and Literature Provenance."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.schemas.patient import EvidenceReference


class FindingProvenance(BaseModel):
    finding_key: str
    finding_name: str
    disease_id: str
    clinical_significance: str
    extract: str
    evidence_tier: str
    literature_references: List[EvidenceReference] = Field(default_factory=list)


class PatientFindingProvenanceItem(BaseModel):
    modality: str  # "LABORATORY", "SYMPTOM", "IMAGING", "TREATMENT"
    feature_name: str
    observed_value: str
    is_abnormal: bool
    provenance: FindingProvenance


class PatientEvidenceProvenance(BaseModel):
    patient_id: str
    disease_id: str
    disease_name: str
    epistemic_confidence_score: float
    total_grounded_findings: int
    findings_provenance: List[PatientFindingProvenanceItem] = Field(default_factory=list)
    disease_level_references: List[EvidenceReference] = Field(default_factory=list)


class EvidenceExplorerSummary(BaseModel):
    total_publications: int
    disease_distribution: Dict[str, int]
    evidence_tier_distribution: Dict[str, int]
    supported_biomarkers_count: int
    registry_citations: List[EvidenceReference] = Field(default_factory=list)
