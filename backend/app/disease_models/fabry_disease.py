"""Fabry Disease Pathophysiological Model (OMIM: 301500, Orpha: 324)."""
import numpy as np
from typing import List, Dict, Any
from app.disease_models.base import BaseDiseaseModel
from app.schemas.patient import (
    DiseaseMetadata, ClinicalSymptom, LabMeasurement, ImagingStudy,
    ImagingParametricFeature, ClinicalEncounterNote, TreatmentResponseScenario,
    CounterfactualTrajectoryPoint, UncertaintyBounds
)
from app.knowledge.evidence_base import evidence_base


class FabryDiseaseModel(BaseDiseaseModel):
    @property
    def disease_id(self) -> str:
        return "fabry_disease"

    @property
    def metadata(self) -> DiseaseMetadata:
        return DiseaseMetadata(
            disease_id="fabry_disease",
            disease_name="Fabry Disease (Anderson-Fabry Disease)",
            omim_id="#301500",
            orpha_code="ORPHA:324",
            genetic_basis="X-linked mutations in the GLA gene (encoding alpha-galactosidase A) at Xq22.1",
            prevalence="Estimated 1 in 40,000 to 1 in 117,000 live male births",
            inheritance="X-linked"
        )

    @property
    def supported_phenotypes(self) -> List[str]:
        return ["Classic Early-Onset", "Cardiac Variant Late-Onset", "Renal Variant"]

    @property
    def evidence_keys(self) -> List[str]:
        return ["ORPHANET_2010_FABRY", "ORTIZ_2018_CONSENSUS", "NEJM_2001_FABRY_ERT"]

    def generate_symptoms(
        self, age_years: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[ClinicalSymptom]:
        symptoms = []

        # 1. Neuropathic Pain / Acroparesthesias
        symptoms.append(ClinicalSymptom(
            symptom_id="fd_sym_acroparesthesia",
            name="Severe Episodic Burning Extremity Pain (Acroparesthesias)",
            category="Neurological / Peripheral",
            onset_month=max(1, int(rng.integers(1, 4))),
            severity_score=float(np.round(rng.uniform(6.5, 9.5), 1)),
            description="Agonizing burning, tingling neuropathic pain in hands and feet triggered by temperature changes, stress, or fever (Fabry pain crises).",
            is_revealed=True,
            evidence_ids=["ORPHANET_2010_FABRY", "ORTIZ_2018_CONSENSUS"]
        ))

        # 2. Hypohidrosis / Anhidrosis
        symptoms.append(ClinicalSymptom(
            symptom_id="fd_sym_hypohidrosis",
            name="Hypohidrosis / Heat Intolerance",
            category="Autonomic",
            onset_month=max(2, int(rng.integers(3, 7))),
            severity_score=float(np.round(rng.uniform(4.0, 7.0), 1)),
            description="Markedly impaired sweating during exertion resulting in heat exhaustion and flushing.",
            is_revealed=True,
            evidence_ids=["ORPHANET_2010_FABRY"]
        ))

        # 3. Angiokeratomas
        symptoms.append(ClinicalSymptom(
            symptom_id="fd_sym_angiokeratoma",
            name="Cutaneous Angiokeratomas ('Bathing Trunk' Distribution)",
            category="Dermatologic",
            onset_month=max(3, int(rng.integers(4, 9))),
            severity_score=float(np.round(rng.uniform(3.5, 6.5), 1)),
            description="Non-blanching dark red-to-purple punctate maculopapular lesions clustered around umbilicus, groin, and buttocks.",
            is_revealed=False,
            evidence_ids=["ORPHANET_2010_FABRY"]
        ))

        # 4. Exertional Dyspnea & Palpitations
        symptoms.append(ClinicalSymptom(
            symptom_id="fd_sym_cardiac",
            name="Exertional Dyspnea, Chest Tightness, and Palpitations",
            category="Cardiovascular",
            onset_month=max(5, int(rng.integers(6, 14))),
            severity_score=float(np.round(rng.uniform(5.0, 8.0), 1)),
            description="Progressive shortness of breath on exertion and brief episodes of paroxysmal atrial tachycardia.",
            is_revealed=False,
            evidence_ids=["ORTIZ_2018_CONSENSUS"]
        ))

        return symptoms

    def generate_laboratory_trajectories(
        self, current_month: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[LabMeasurement]:
        labs = []

        # 1. Plasma Lyso-Gb3
        lyso_val = float(np.round(np.clip(rng.normal(48.0, 8.5), 22.0, 95.0), 1))
        labs.append(LabMeasurement(
            measurement_id=f"lab_lyso_gb3_m{current_month}",
            test_code="LYSO_GB3",
            test_name="Plasma Globotriaosylsphingosine (Lyso-Gb3)",
            category="Sphingolipid Biomarker",
            value=lyso_val,
            unit="ng/mL",
            ref_low=0.0,
            ref_high=0.8,
            is_abnormal=(lyso_val > 0.8),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=lyso_val,
                ci_95_low=round(lyso_val - 1.96 * 8.5, 1),
                ci_95_high=round(lyso_val + 1.96 * 8.5, 1),
                aleatoric_variance=8.5 ** 2,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["ORTIZ_2018_CONSENSUS", "ORPHANET_2010_FABRY"]),
                uncertainty_source="Liquid chromatography-tandem mass spectrometry (LC-MS/MS) calibration limit"
            ),
            evidence_ids=["ORTIZ_2018_CONSENSUS", "ORPHANET_2010_FABRY"],
            ordered=False,
            reported=False
        ))

        # 2. Leukocyte Alpha-Galactosidase A Activity
        enzyme_val = float(np.round(np.clip(rng.normal(0.4, 0.15), 0.05, 1.1), 2))
        labs.append(LabMeasurement(
            measurement_id=f"lab_alpha_gal_m{current_month}",
            test_code="ALPHA_GALACTOSIDASE_A",
            test_name="Leukocyte Alpha-Galactosidase A Activity",
            category="Enzymatic Assay",
            value=enzyme_val,
            unit="nmol/h/mg protein",
            ref_low=4.0,
            ref_high=18.0,
            is_abnormal=(enzyme_val < 4.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=enzyme_val,
                ci_95_low=round(max(0.01, enzyme_val - 1.96 * 0.15), 2),
                ci_95_high=round(enzyme_val + 1.96 * 0.15, 2),
                aleatoric_variance=0.0225,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["ORPHANET_2010_FABRY"]),
                uncertainty_source="Fluorometric 4-MU assay precision variance"
            ),
            evidence_ids=["ORPHANET_2010_FABRY"],
            ordered=False,
            reported=False
        ))

        # 3. 24-Hour Urine Protein / Microalbuminuria
        protein_val = float(np.round(np.clip(rng.normal(820.0, 110.0), 380.0, 1600.0), 0))
        labs.append(LabMeasurement(
            measurement_id=f"lab_uprot_m{current_month}",
            test_code="URINE_PROTEIN_24H",
            test_name="24-Hour Urine Protein Excretion",
            category="Renal Function",
            value=protein_val,
            unit="mg/24h",
            ref_low=0.0,
            ref_high=150.0,
            is_abnormal=(protein_val > 150.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=protein_val,
                ci_95_low=round(protein_val - 1.96 * 60.0, 0),
                ci_95_high=round(protein_val + 1.96 * 60.0, 0),
                aleatoric_variance=3600.0,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["ORTIZ_2018_CONSENSUS"]),
                uncertainty_source="Pyrogallol red turbidimetric assay variability"
            ),
            evidence_ids=["ORTIZ_2018_CONSENSUS"],
            ordered=False,
            reported=False
        ))

        # 4. Serum Creatinine & eGFR
        creat_val = float(np.round(np.clip(rng.normal(1.45, 0.18), 1.05, 2.4), 2))
        labs.append(LabMeasurement(
            measurement_id=f"lab_creat_m{current_month}",
            test_code="SERUM_CREATININE",
            test_name="Serum Creatinine",
            category="Renal Function",
            value=creat_val,
            unit="mg/dL",
            ref_low=0.6,
            ref_high=1.2,
            is_abnormal=(creat_val > 1.2),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=creat_val,
                ci_95_low=round(creat_val - 1.96 * 0.1, 2),
                ci_95_high=round(creat_val + 1.96 * 0.1, 2),
                aleatoric_variance=0.01,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["ORTIZ_2018_CONSENSUS"]),
                uncertainty_source="IDMS-traceable enzymatic creatinine measurement"
            ),
            evidence_ids=["ORTIZ_2018_CONSENSUS"],
            ordered=False,
            reported=False
        ))

        return labs

    def generate_imaging_studies(
        self, current_month: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[ImagingStudy]:
        return [
            ImagingStudy(
                study_id="img_mri_cardiac_fd",
                modality="Cardiac MRI with Parametric T1 Mapping & LGE",
                anatomical_region="Heart / Myocardium",
                timestamp_month=current_month,
                acronym="CMR-T1-MAP",
                acr_findings=(
                    "Concentric left ventricular hypertrophy with maximal wall thickness of 17 mm in the interventricular "
                    "septum and 15 mm in the posterior wall (indexed LV mass 115 g/m2). Native myocardial T1 mapping demonstrates "
                    "abnormally low non-contrast T1 values (840 ms, normal reference 950-1050 ms), reflecting widespread intracellular "
                    "sphingolipid storage. Late gadolinium enhancement (LGE) reveals focal non-ischemic mid-wall enhancement localized to the "
                    "basal inferolateral wall of the left ventricle."
                ),
                radiology_impression=(
                    "1. Low native myocardial T1 values in the setting of left ventricular hypertrophy is pathognomonic for cardiac Fabry disease.\n"
                    "2. Focal basal inferolateral LGE indicates established focal myocardial replacement fibrosis."
                ),
                parametric_features=[
                    ImagingParametricFeature(
                        feature_name="Native Myocardial T1 Time",
                        z_score=-3.8,
                        quantitative_value=840.0,
                        unit="ms",
                        attenuation_or_signal="Markedly Shortened T1",
                        organ="Left Ventricular Myocardium"
                    ),
                    ImagingParametricFeature(
                        feature_name="Interventricular Septal Thickness",
                        z_score=3.2,
                        quantitative_value=17.0,
                        unit="mm",
                        attenuation_or_signal="Hypertrophied",
                        organ="Interventricular Septum"
                    )
                ],
                pathological_signs=["Low Native Myocardial T1 Mapping", "Basal Inferolateral Wall Late Gadolinium Enhancement"],
                evidence_ids=["ORTIZ_2018_CONSENSUS", "ORPHANET_2010_FABRY"],
                ordered=False,
                reported=False,
                schematic_data={
                    "type": "cardiac_short_axis_slice",
                    "septal_thickness_mm": 17.0,
                    "t1_shortening_ms": 840,
                    "lge_inferolateral": True
                }
            )
        ]

    def generate_encounter_notes(
        self, current_month: int, disease_stage: str, symptoms: List[ClinicalSymptom], rng: np.random.Generator
    ) -> List[ClinicalEncounterNote]:
        return [
            ClinicalEncounterNote(
                encounter_id=f"enc_fd_m{current_month}",
                timestamp_month=current_month,
                encounter_type="Cardiorenal Consultation",
                chief_complaint="Severe burning extremity pain, inability to sweat, and unexplained left ventricular hypertrophy.",
                hpi=(
                    "Patient reports lifelong history of painful episodes in palms and soles exacerbated by warm weather and exercise. "
                    "Recently evaluated for unexplained concentric left ventricular hypertrophy and new-onset proteinuria during routine health screening. "
                    "Maternal uncle had reported unexplained heart failure and hemodialysis dependency in his late forties."
                ),
                physical_exam={
                    "General": "Well-nourished individual appearing uncomfortable with warm ambient examination room temperature.",
                    "Skin": "Multiple 1-3 mm dark purplish keratotic papules over the periumbilical region and bilateral flanks.",
                    "Cardiovascular": "S4 gallop audible at apex. Sustained apical impulse. Normal S1/S2 without murmurs.",
                    "Neurological": "Hyperalgesia to light pinprick on both feet with intact proprioception and motor power."
                },
                assessment_and_plan=(
                    "Syndromic multisystem presentation with acroparesthesias, hypohidrosis, angiokeratomas, LVH, and proteinuria. "
                    "High clinical suspicion for X-linked Fabry disease. "
                    "Plan: Diagnostic plasma lyso-Gb3 quantification, leukocyte alpha-galactosidase A enzyme analysis, GLA gene sequencing, and cardiac MRI."
                ),
                disease_stage=disease_stage
            )
        ]

    def generate_treatment_scenarios(
        self, current_month: int, disease_stage: str, phenotype: str
    ) -> List[TreatmentResponseScenario]:
        return [
            TreatmentResponseScenario(
                scenario_id="fd_scen_ert_prompt",
                name="Enzyme Replacement Therapy (Agalsidase beta 1.0 mg/kg q2w)",
                intervention_type="Targeted Therapy",
                description="Biweekly intravenous recombinant human alpha-galactosidase A combined with renal-protective ACE-inhibitor therapy.",
                evidence_ids=["NEJM_2001_FABRY_ERT", "ORTIZ_2018_CONSENSUS"],
                trajectory=[
                    CounterfactualTrajectoryPoint(
                        month=current_month, state_score=0.72, primary_biomarker_value=48.0, clinical_status="Baseline: Elevated lyso-Gb3, progressive proteinuria & LVH", ci_low=42.0, ci_high=54.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 3, state_score=0.55, primary_biomarker_value=18.0, clinical_status="Month 3: Rapid ~60% clearance of plasma lyso-Gb3; reduction in pain crisis frequency", ci_low=14.0, ci_high=22.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 6, state_score=0.42, primary_biomarker_value=11.5, clinical_status="Month 6: Proteinuria stabilized (<400 mg/24h); improved sweat production", ci_low=8.5, ci_high=14.5
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 12, state_score=0.30, primary_biomarker_value=7.2, clinical_status="Month 12: Arrest of progressive LV remodeling and preservation of glomerular filtration", ci_low=5.0, ci_high=9.5
                    )
                ],
                is_active=True
            )
        ]

    def get_physiological_constraints(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "FD_RULE_LYSO_GB3_ELEVATION",
                "name": "Plasma Lyso-Gb3 Elevation Bound",
                "category": "Physiological Range",
                "test_code": "LYSO_GB3",
                "min_value": 0.8,
                "severity": "FATAL_ERROR",
                "description": "Plasma Lyso-Gb3 must be elevated above normal threshold (>0.8 ng/mL) in symptomatic classic Fabry disease."
            },
            {
                "rule_id": "FD_RULE_ALPHA_GAL_DEFICIENCY",
                "name": "Alpha-Galactosidase A Deficiency Bound",
                "category": "Physiological Range",
                "test_code": "ALPHA_GALACTOSIDASE_A",
                "max_value": 3.0,
                "severity": "FATAL_ERROR",
                "description": "Leukocyte alpha-galactosidase A activity in affected males must be subnormal (<3.0 nmol/h/mg)."
            }
        ]
