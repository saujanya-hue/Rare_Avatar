"""Evidence ingestion, retrieval, and attribution engine.

Grounds rare-disease patient avatars, diagnostic assertions, and clinical consistency
rules directly in PubMed literature citations and clinical trial evidence.
"""
from typing import Dict, List, Optional, Any
from app.knowledge.literature_data import LITERATURE_REGISTRY
from app.schemas.patient import EvidenceReference, SyntheticPatientSpecification


DISEASE_EVIDENCE_MAP: Dict[str, List[str]] = {
    "wilson_disease": ["EASL_2012_GUIDELINES", "LANCET_2015_WILSON", "FERENCI_2003_CLASSIF"],
    "fabry_disease": ["ORPHANET_2010_FABRY", "ORTIZ_2018_CONSENSUS", "NEJM_2001_FABRY_ERT"],
    "gaucher_disease": ["SEMINARS_2004_GAUCHER", "REGISTRY_2000_GAUCHER"]
}

FINDING_PROVENANCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Wilson Disease Findings
    "CERULOPLASMIN": {
        "finding_name": "Serum Ceruloplasmin Deficiency",
        "disease_id": "wilson_disease",
        "evidence_ids": ["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"],
        "clinical_significance": "Leipzig Diagnostic Criteria: Ceruloplasmin < 0.10 g/L (10 mg/dL) contributes 2 points; 0.10-0.20 g/L contributes 1 point.",
        "extract": "Serum ceruloplasmin is typically low (<20 mg/dL) in 85-90% of symptomatic Wilson patients due to impaired holoceruloplasmin synthesis.",
        "evidence_tier": "Level A (Clinical Practice Guideline)"
    },
    "COPPER_24H": {
        "finding_name": "24-Hour Urinary Copper Excretion",
        "disease_id": "wilson_disease",
        "evidence_ids": ["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"],
        "clinical_significance": "Urinary copper excretion > 100 ug/24h (>1.6 umol/24h) contributes 2 points toward definitive diagnosis.",
        "extract": "Active disease is characterized by non-ceruloplasmin bound copper hypercupriuresis reflecting systemic copper overload.",
        "evidence_tier": "Level A (Clinical Practice Guideline)"
    },
    "FREE_COPPER": {
        "finding_name": "Non-Ceruloplasmin Bound (Free) Copper",
        "disease_id": "wilson_disease",
        "evidence_ids": ["EASL_2012_GUIDELINES"],
        "clinical_significance": "Calculated non-ceruloplasmin copper > 15-25 ug/dL indicates circulating toxic copper pool.",
        "extract": "Free serum copper is calculated as Total Copper (ug/dL) - [Ceruloplasmin (mg/dL) x 3.15].",
        "evidence_tier": "Level A (Clinical Practice Guideline)"
    },
    "KAYSER_FLEISCHER": {
        "finding_name": "Kayser-Fleischer Corneal Copper Rings",
        "disease_id": "wilson_disease",
        "evidence_ids": ["EASL_2012_GUIDELINES", "LANCET_2015_WILSON"],
        "clinical_significance": "Present in >95% of neurological Wilson presentations; contributes 2 Leipzig points.",
        "extract": "Slit-lamp examination reveals golden-brown copper granules in Descemet's membrane at the corneal limbus.",
        "evidence_tier": "Level A (Systematic Seminar)"
    },
    "BASAL_GANGLIA_MRI": {
        "finding_name": "Basal Ganglia MRI T2 Hyperintensities & Panda Sign",
        "disease_id": "wilson_disease",
        "evidence_ids": ["LANCET_2015_WILSON"],
        "clinical_significance": "Pathognomonic neuroimaging changes reflecting copper deposition in lenticular nuclei.",
        "extract": "Bilateral symmetrical hyperintensity on T2-weighted MRI in putamen, caudate, and midbrain tectum ('face of giant panda').",
        "evidence_tier": "Level A (Systematic Seminar)"
    },

    # Fabry Disease Findings
    "LYSO_GB3": {
        "finding_name": "Plasma Globotriaosylsphingosine (Lyso-Gb3)",
        "disease_id": "fabry_disease",
        "evidence_ids": ["ORTIZ_2018_CONSENSUS", "ORPHANET_2010_FABRY"],
        "clinical_significance": "Most sensitive biochemical biomarker for disease activity, phenotype severity, and treatment monitoring.",
        "extract": "Plasma Lyso-Gb3 is elevated >10-fold in classic males and serves as an independent predictor of long-term cardiovascular and renal risk.",
        "evidence_tier": "Level A (International Consensus Guideline)"
    },
    "ALPHA_GAL_A": {
        "finding_name": "Alpha-Galactosidase A Enzyme Deficiency",
        "disease_id": "fabry_disease",
        "evidence_ids": ["ORPHANET_2010_FABRY"],
        "clinical_significance": "Definitive biochemical diagnosis in males: leukocyte or plasma activity <5% of normal mean.",
        "extract": "X-linked GLA mutations lead to loss of lysosomal alpha-galactosidase A and multi-system neutral glycosphingolipid storage.",
        "evidence_tier": "Level A (Rare Disease Review)"
    },
    "ACROPARESTHESIA": {
        "finding_name": "Neuropathic Extremity Acroparesthesias",
        "disease_id": "fabry_disease",
        "evidence_ids": ["ORPHANET_2010_FABRY", "NEJM_2001_FABRY_ERT"],
        "clinical_significance": "Cardinal early clinical hallmark triggered by thermal changes, exertion, or febrile illness.",
        "extract": "Burning, lancinating acral pain resulting from selective small-fiber A-delta and C sensory neuron glycolipid infiltration.",
        "evidence_tier": "Level A (Randomized Controlled Trial)"
    },
    "LVH_CARDIAC": {
        "finding_name": "Concentric Left Ventricular Hypertrophy (LVH)",
        "disease_id": "fabry_disease",
        "evidence_ids": ["ORTIZ_2018_CONSENSUS"],
        "clinical_significance": "Principal cause of adult premature morbidity; myocardial fibrosis typically begins in posterolateral wall.",
        "extract": "Non-obstructive concentric hypertrophy with disproportionately decreased native T1 relaxation times on cardiac MRI.",
        "evidence_tier": "Level A (International Consensus Guideline)"
    },
    "PROTEINURIA": {
        "finding_name": "Microalbuminuria & Progressive Proteinuria",
        "disease_id": "fabry_disease",
        "evidence_ids": ["ORTIZ_2018_CONSENSUS", "NEJM_2001_FABRY_ERT"],
        "clinical_significance": "Indicator of progressive podocyte vacuolization and glomerulosclerosis.",
        "extract": "Glomerular filtration rate decline of 2-5 mL/min/1.73m2/year in untreated adult classical males.",
        "evidence_tier": "Level A (International Consensus Guideline)"
    },

    # Gaucher Disease Type 1 Findings
    "LYSO_GB1": {
        "finding_name": "Glucosylsphingosine (Lyso-Gb1) Elevation",
        "disease_id": "gaucher_disease",
        "evidence_ids": ["REGISTRY_2000_GAUCHER", "SEMINARS_2004_GAUCHER"],
        "clinical_significance": "Superior longitudinal monitoring biomarker correlating with organomegaly and marrow burden.",
        "extract": "Plasma Lyso-Gb1 demonstrates >99% diagnostic sensitivity and specificity, far outperforming chitotriosidase.",
        "evidence_tier": "Level A (Large Registry Cohort)"
    },
    "BETA_GLUCOSIDASE": {
        "finding_name": "Acid Beta-Glucosidase (Glucocerebrosidase) Deficiency",
        "disease_id": "gaucher_disease",
        "evidence_ids": ["SEMINARS_2004_GAUCHER"],
        "clinical_significance": "Gold standard diagnostic test: enzyme activity in leukocytes <15% of control values.",
        "extract": "Biallelic GBA1 mutations impair lysosomal degradation of glucocerebroside into glucose and ceramide.",
        "evidence_tier": "Level B (Clinical Consensus Review)"
    },
    "SPLENOMEGALY": {
        "finding_name": "Massive Hypersplenomegaly",
        "disease_id": "gaucher_disease",
        "evidence_ids": ["REGISTRY_2000_GAUCHER", "SEMINARS_2004_GAUCHER"],
        "clinical_significance": "Present in 87% of untreated registry patients (spleen volume 5 to 25 times normal).",
        "extract": "Splenic enlargement results from intense sinusoidal infiltration of lipid-engorged Gaucher histiocytes.",
        "evidence_tier": "Level A (Large Registry Cohort)"
    },
    "THROMBOCYTOPENIA": {
        "finding_name": "Hypersplenic Thrombocytopenia & Anemia",
        "disease_id": "gaucher_disease",
        "evidence_ids": ["REGISTRY_2000_GAUCHER", "SEMINARS_2004_GAUCHER"],
        "clinical_significance": "Most frequent hematological manifestation causing bleeding diathesis and easy bruising.",
        "extract": "Peripheral platelet counts <120,000/uL caused by splenic sequestration and marrow replacement.",
        "evidence_tier": "Level A (Large Registry Cohort)"
    },
    "ERLENMEYER_FLASK": {
        "finding_name": "Erlenmeyer Flask Femoral Deformity",
        "disease_id": "gaucher_disease",
        "evidence_ids": ["SEMINARS_2004_GAUCHER"],
        "clinical_significance": "Pathognomonic osseous remodeling sign present in >60% of Type 1 patients.",
        "extract": "Failure of normal cortical modeling of distal femur leading to characteristic flaring and cortical thinning.",
        "evidence_tier": "Level B (Clinical Consensus Review)"
    }
}


class EvidenceBase:
    def __init__(self):
        self._registry: Dict[str, EvidenceReference] = {
            k: EvidenceReference(**v) for k, v in LITERATURE_REGISTRY.items()
        }

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceReference]:
        return self._registry.get(evidence_id)

    def get_all_references(self) -> List[EvidenceReference]:
        return list(self._registry.values())

    def get_evidence_by_disease(self, disease_id: str) -> List[EvidenceReference]:
        ids = DISEASE_EVIDENCE_MAP.get(disease_id, [])
        return [self._registry[i] for i in ids if i in self._registry]

    def search_literature(self, query: str, disease_id: Optional[str] = None) -> List[EvidenceReference]:
        query_lower = query.lower()
        results = []
        for ref in self._registry.values():
            if disease_id and disease_id in DISEASE_EVIDENCE_MAP:
                if ref.evidence_id not in DISEASE_EVIDENCE_MAP[disease_id]:
                    continue

            if (
                query_lower in ref.title.lower()
                or query_lower in ref.relevance_summary.lower()
                or query_lower in ref.authors.lower()
                or (ref.pmid and query_lower in ref.pmid)
                or query_lower in ref.journal.lower()
            ):
                results.append(ref)
        return results

    def get_finding_provenance(self, finding_key: str, disease_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        key_upper = finding_key.upper()
        # Direct key match or substring match
        matched_key = None
        for k in FINDING_PROVENANCE_REGISTRY:
            if k == key_upper or k in key_upper or key_upper in k:
                matched_key = k
                break

        if not matched_key:
            return None

        data = FINDING_PROVENANCE_REGISTRY[matched_key]
        if disease_id and data["disease_id"] != disease_id:
            return None

        refs = [self._registry[eid] for eid in data["evidence_ids"] if eid in self._registry]
        return {
            "finding_key": matched_key,
            "finding_name": data["finding_name"],
            "disease_id": data["disease_id"],
            "clinical_significance": data["clinical_significance"],
            "extract": data["extract"],
            "evidence_tier": data["evidence_tier"],
            "literature_references": refs
        }

    def get_patient_provenance(self, patient: SyntheticPatientSpecification) -> Dict[str, Any]:
        d_id = patient.disease.disease_id
        provenance_items = []

        # Map laboratory tests
        for lab in patient.lab_history:
            prov = self.get_finding_provenance(lab.test_code, d_id)
            if prov:
                provenance_items.append({
                    "modality": "LABORATORY",
                    "feature_name": getattr(lab, "test_name", lab.test_code),
                    "observed_value": f"{lab.value} {lab.unit}",
                    "is_abnormal": lab.is_abnormal,
                    "provenance": prov
                })

        # Map symptoms
        for sym in patient.symptoms:
            prov = self.get_finding_provenance(sym.name, d_id) or self.get_finding_provenance(sym.symptom_id, d_id)
            if prov:
                provenance_items.append({
                    "modality": "SYMPTOM",
                    "feature_name": sym.name,
                    "observed_value": f"Severity {sym.severity_score}/10, Onset {sym.onset_month}m",
                    "is_abnormal": True,
                    "provenance": prov
                })

        # Map imaging studies
        for img in patient.imaging_studies:
            study_label = getattr(img, "modality", getattr(img, "acronym", "Imaging Study"))
            for feat in img.parametric_features:
                prov = self.get_finding_provenance(feat.feature_name, d_id)
                if prov:
                    provenance_items.append({
                        "modality": "IMAGING",
                        "feature_name": f"{study_label}: {feat.feature_name}",
                        "observed_value": f"{feat.quantitative_value} {feat.unit or ''}".strip(),
                        "is_abnormal": True,
                        "provenance": prov
                    })

        disease_refs = self.get_evidence_by_disease(d_id)
        confidence = self.compute_epistemic_confidence([r.evidence_id for r in disease_refs])

        return {
            "patient_id": patient.patient_id,
            "disease_id": d_id,
            "disease_name": patient.disease.disease_name,
            "epistemic_confidence_score": confidence,
            "total_grounded_findings": len(provenance_items),
            "findings_provenance": provenance_items,
            "disease_level_references": disease_refs
        }

    def compute_epistemic_confidence(self, evidence_ids: List[str]) -> float:
        if not evidence_ids:
            return 0.10

        score = 0.0
        for eid in evidence_ids:
            ref = self.get_evidence(eid)
            if not ref:
                continue
            if "Level A" in ref.evidence_level:
                score += 0.40
            elif "Level B" in ref.evidence_level:
                score += 0.25
            else:
                score += 0.15

        return min(round(score, 2), 0.98)


evidence_base = EvidenceBase()
