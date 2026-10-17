"""Unit and Integration Tests for Evidence Explorer and Finding Provenance."""
import pytest
from fastapi.testclient import TestClient

from app.main import app, bootstrap_initial_avatars
from app.knowledge.evidence_base import evidence_base
from app.schemas.evidence import PatientEvidenceProvenance, FindingProvenance, EvidenceExplorerSummary


@pytest.fixture(scope="module", autouse=True)
def init_app():
    bootstrap_initial_avatars()


@pytest.fixture
def client():
    return TestClient(app)


def test_evidence_base_core_retrieval():
    """Verify literature references are correctly indexed and retrievable."""
    all_refs = evidence_base.get_all_references()
    assert len(all_refs) >= 8

    # Check for real PubMed IDs
    pmids = [r.pmid for r in all_refs if r.pmid]
    assert len(pmids) >= 8
    assert "22342623" in pmids  # EASL 2012 Wilson Guidelines
    assert "29530430" in pmids  # Ortiz 2018 Fabry Consensus
    assert "15467978" in pmids  # Pastores 2004 Gaucher Guidelines


def test_evidence_by_disease_mapping():
    """Verify literature references are mapped to their respective rare diseases."""
    wd_refs = evidence_base.get_evidence_by_disease("wilson_disease")
    fd_refs = evidence_base.get_evidence_by_disease("fabry_disease")
    gd_refs = evidence_base.get_evidence_by_disease("gaucher_disease")

    assert len(wd_refs) >= 3
    assert len(fd_refs) >= 3
    assert len(gd_refs) >= 2


def test_finding_provenance_mapping():
    """Verify individual biomarkers and symptoms map to substantiated literature extracts."""
    cp_prov = evidence_base.get_finding_provenance("CERULOPLASMIN")
    assert cp_prov is not None
    assert cp_prov["disease_id"] == "wilson_disease"
    assert len(cp_prov["literature_references"]) > 0
    assert "Leipzig" in cp_prov["clinical_significance"]

    lyso3_prov = evidence_base.get_finding_provenance("LYSO_GB3")
    assert lyso3_prov is not None
    assert lyso3_prov["disease_id"] == "fabry_disease"

    lyso1_prov = evidence_base.get_finding_provenance("LYSO_GB1")
    assert lyso1_prov is not None
    assert lyso1_prov["disease_id"] == "gaucher_disease"


def test_evidence_explorer_api_routes(client):
    """Test REST API routes for Evidence Explorer."""
    # 1. Summary
    sum_resp = client.get("/api/evidence/summary")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["total_publications"] >= 8
    assert summary["supported_biomarkers_count"] > 0

    # 2. Search
    search_resp = client.get("/api/evidence/search?q=copper")
    assert search_resp.status_code == 200
    search_results = search_resp.json()
    assert len(search_results) > 0

    # 3. Provenance for active patient
    p_resp = client.get("/api/patients")
    patients = p_resp.json()
    p_id = patients[0]["patient_id"]

    prov_resp = client.get(f"/api/evidence/provenance/{p_id}")
    assert prov_resp.status_code == 200
    prov_data = prov_resp.json()
    assert prov_data["patient_id"] == p_id
    assert prov_data["epistemic_confidence_score"] > 0.0
    assert len(prov_data["findings_provenance"]) > 0

    # 4. Catalog
    cat_resp = client.get("/api/evidence/catalog")
    assert cat_resp.status_code == 200
    catalog = cat_resp.json()
    assert len(catalog) >= 10
