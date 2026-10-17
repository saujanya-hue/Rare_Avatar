"""REST API routes for Medical Evidence and Literature Grounding."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.schemas.patient import EvidenceReference
from app.schemas.evidence import (
    FindingProvenance, PatientEvidenceProvenance, EvidenceExplorerSummary
)
from app.knowledge.evidence_base import evidence_base, FINDING_PROVENANCE_REGISTRY, DISEASE_EVIDENCE_MAP
from app.disease_models import disease_registry
from app.engine.state_manager import state_manager

router = APIRouter(prefix="/api/evidence", tags=["Medical Evidence & Literature"])


@router.get("/list", response_model=List[EvidenceReference])
def list_all_evidence():
    """List all peer-reviewed PubMed literature references indexed in RareAvatar."""
    return evidence_base.get_all_references()


@router.get("/search", response_model=List[EvidenceReference])
def search_evidence(
    q: str = Query(..., min_length=2),
    disease_id: Optional[str] = Query(None)
):
    """Search literature citations by keyword, title, PMID, or author with optional disease filter."""
    return evidence_base.search_literature(q, disease_id=disease_id)


@router.get("/diseases")
def list_supported_diseases():
    """List all supported rare disease models with genetic loci and registry links."""
    return disease_registry.list_available_diseases()


@router.get("/by-disease/{disease_id}", response_model=List[EvidenceReference])
def get_evidence_for_disease(disease_id: str):
    """Retrieve all literature records supporting a specific rare disease model."""
    refs = evidence_base.get_evidence_by_disease(disease_id)
    if not refs:
        raise HTTPException(status_code=404, detail=f"No literature references found for disease '{disease_id}'.")
    return refs


@router.get("/provenance/{patient_id}", response_model=PatientEvidenceProvenance)
def get_patient_evidence_provenance(patient_id: str):
    """
    Retrieve comprehensive literature provenance mapping for the active patient avatar:
    maps all symptoms, laboratory tests, imaging findings, and therapies directly to PubMed citations.
    """
    patient = state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient avatar '{patient_id}' not found.")

    provenance_data = evidence_base.get_patient_provenance(patient)
    return PatientEvidenceProvenance(**provenance_data)


@router.get("/finding/{finding_key}", response_model=FindingProvenance)
def inspect_finding_provenance(finding_key: str, disease_id: Optional[str] = None):
    """Retrieve clinical significance, PubMed citations, and guideline extracts for an individual finding."""
    prov = evidence_base.get_finding_provenance(finding_key, disease_id=disease_id)
    if not prov:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_key}' not found in provenance registry.")
    return FindingProvenance(**prov)


@router.get("/catalog", response_model=List[FindingProvenance])
def get_finding_provenance_catalog():
    """Retrieve full catalog of supported biomarker and phenotypic finding provenances."""
    catalog = []
    for k in FINDING_PROVENANCE_REGISTRY:
        data = evidence_base.get_finding_provenance(k)
        if data:
            catalog.append(FindingProvenance(**data))
    return catalog


@router.get("/summary", response_model=EvidenceExplorerSummary)
def get_evidence_explorer_summary():
    """Retrieve high-level metrics and distributions for the PubMed literature registry."""
    all_refs = evidence_base.get_all_references()

    # Disease distribution
    d_dist: Dict[str, int] = {}
    for d_id, eids in DISEASE_EVIDENCE_MAP.items():
        d_dist[d_id] = len(eids)

    # Evidence tier distribution
    tier_dist: Dict[str, int] = {}
    for ref in all_refs:
        t = ref.evidence_level.split(" (")[0] if " (" in ref.evidence_level else ref.evidence_level
        tier_dist[t] = tier_dist.get(t, 0) + 1

    return EvidenceExplorerSummary(
        total_publications=len(all_refs),
        disease_distribution=d_dist,
        evidence_tier_distribution=tier_dist,
        supported_biomarkers_count=len(FINDING_PROVENANCE_REGISTRY),
        registry_citations=all_refs
    )


@router.get("/{evidence_id}", response_model=EvidenceReference)
def get_evidence_detail(evidence_id: str):
    """Retrieve full PubMed citation record by unique evidence identifier."""
    ref = evidence_base.get_evidence(evidence_id)
    if not ref:
        raise HTTPException(status_code=404, detail=f"Evidence reference '{evidence_id}' not found.")
    return ref
