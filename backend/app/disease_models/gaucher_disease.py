"""Gaucher Disease Type 1 Pathophysiological Model (OMIM: 230800, Orpha: 355)."""
import numpy as np
from typing import List, Dict, Any
from app.disease_models.base import BaseDiseaseModel
from app.schemas.patient import (
    DiseaseMetadata, ClinicalSymptom, LabMeasurement, ImagingStudy,
    ImagingParametricFeature, ClinicalEncounterNote, TreatmentResponseScenario,
    CounterfactualTrajectoryPoint, UncertaintyBounds
)
from app.knowledge.evidence_base import evidence_base


class GaucherDiseaseModel(BaseDiseaseModel):
    @property
    def disease_id(self) -> str:
        return "gaucher_disease"

    @property
    def metadata(self) -> DiseaseMetadata:
        return DiseaseMetadata(
            disease_id="gaucher_disease",
            disease_name="Gaucher Disease Type 1 (Non-Neuronopathic)",
            omim_id="#230800",
            orpha_code="ORPHA:355",
            genetic_basis="Autosomal recessive mutations in the GBA1 gene (acid beta-glucosidase) on chromosome 1q22",
            prevalence="Estimated 1 in 40,000 to 1 in 60,000; up to 1 in 800 in Ashkenazi Jewish ancestry",
            inheritance="Autosomal Recessive"
        )

    @property
    def supported_phenotypes(self) -> List[str]:
        return ["Classic Non-Neuronopathic Type 1", "Skeletal Predominant", "Hematologic-Visceral"]

    @property
    def evidence_keys(self) -> List[str]:
        return ["SEMINARS_2004_GAUCHER", "REGISTRY_2000_GAUCHER"]

    def generate_symptoms(
        self, age_years: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[ClinicalSymptom]:
        symptoms = []

        # 1. Splenomegaly & Early Satiety
        symptoms.append(ClinicalSymptom(
            symptom_id="gd_sym_splenomegaly",
            name="Abdominal Protuberance, Early Satiety, and Left Flank Heaviness",
            category="Visceral / Gastrointestinal",
            onset_month=max(1, int(rng.integers(2, 6))),
            severity_score=float(np.round(rng.uniform(6.0, 9.0), 1)),
            description="Noticeable progressive abdominal enlargement, left upper quadrant dragging sensation, and inability to eat full meals.",
            is_revealed=True,
            evidence_ids=["SEMINARS_2004_GAUCHER", "REGISTRY_2000_GAUCHER"]
        ))

        # 2. Easy Bruising & Epistaxis
        symptoms.append(ClinicalSymptom(
            symptom_id="gd_sym_bleeding",
            name="Spontaneous Ecchymoses, Mucosal Bleeding, and Petechiae",
            category="Hematologic",
            onset_month=max(2, int(rng.integers(3, 8))),
            severity_score=float(np.round(rng.uniform(5.5, 8.5), 1)),
            description="Recurrent nosebleeds, prolonged bleeding from minor abrasions, and extensive spontaneous purpura on limbs.",
            is_revealed=True,
            evidence_ids=["REGISTRY_2000_GAUCHER"]
        ))

        # 3. Bone Pain & Deep Skeletal Aches
        symptoms.append(ClinicalSymptom(
            symptom_id="gd_sym_bone_pain",
            name="Deep Skeletal Bone Pain and Acute Bone Crises",
            category="Musculoskeletal",
            onset_month=max(3, int(rng.integers(4, 11))),
            severity_score=float(np.round(rng.uniform(5.0, 8.5), 1)),
            description="Dull chronic gnawing pain in long bones of thighs and shins with periodic excruciating acute bone crises.",
            is_revealed=False,
            evidence_ids=["SEMINARS_2004_GAUCHER"]
        ))

        return symptoms

    def generate_laboratory_trajectories(
        self, current_month: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[LabMeasurement]:
        labs = []

        # 1. Plasma Lyso-Gb1 (Glucosylsphingosine)
        lyso_val = float(np.round(np.clip(rng.normal(125.0, 22.0), 45.0, 280.0), 1))
        labs.append(LabMeasurement(
            measurement_id=f"lab_lyso_gb1_m{current_month}",
            test_code="LYSO_GB1",
            test_name="Plasma Glucosylsphingosine (Lyso-Gb1)",
            category="Gaucher Lipid Biomarker",
            value=lyso_val,
            unit="ng/mL",
            ref_low=0.0,
            ref_high=1.5,
            is_abnormal=(lyso_val > 1.5),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=lyso_val,
                ci_95_low=round(lyso_val - 1.96 * 22.0, 1),
                ci_95_high=round(lyso_val + 1.96 * 22.0, 1),
                aleatoric_variance=22.0 ** 2,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["REGISTRY_2000_GAUCHER", "SEMINARS_2004_GAUCHER"]),
                uncertainty_source="Tandem mass spectrometry internal standard calibration error"
            ),
            evidence_ids=["REGISTRY_2000_GAUCHER", "SEMINARS_2004_GAUCHER"],
            ordered=False,
            reported=False
        ))

        # 2. Leukocyte Beta-Glucosidase Activity
        enzyme_val = float(np.round(np.clip(rng.normal(0.65, 0.18), 0.1, 1.4), 2))
        labs.append(LabMeasurement(
            measurement_id=f"lab_beta_glucosidase_m{current_month}",
            test_code="BETA_GLUCOSIDASE",
            test_name="Leukocyte Acid Beta-Glucosidase (Glucocerebrosidase)",
            category="Enzymatic Assay",
            value=enzyme_val,
            unit="nmol/h/mg protein",
            ref_low=4.0,
            ref_high=12.0,
            is_abnormal=(enzyme_val < 4.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=enzyme_val,
                ci_95_low=round(max(0.05, enzyme_val - 1.96 * 0.18), 2),
                ci_95_high=round(enzyme_val + 1.96 * 0.18, 2),
                aleatoric_variance=0.0324,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["SEMINARS_2004_GAUCHER"]),
                uncertainty_source="Fluorometric substrate cleavage variance"
            ),
            evidence_ids=["SEMINARS_2004_GAUCHER"],
            ordered=False,
            reported=False
        ))

        # 3. Platelet Count (Severe thrombocytopenia due to hypersplenism)
        plt_val = float(np.round(np.clip(rng.normal(68.0, 12.0), 38.0, 105.0), 0))
        labs.append(LabMeasurement(
            measurement_id=f"lab_plt_gd_m{current_month}",
            test_code="PLATELETS",
            test_name="Platelet Count",
            category="Hematology",
            value=plt_val,
            unit="x10^3/uL",
            ref_low=150.0,
            ref_high=450.0,
            is_abnormal=(plt_val < 150.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=plt_val,
                ci_95_low=round(plt_val - 1.96 * 8.0, 0),
                ci_95_high=round(plt_val + 1.96 * 8.0, 0),
                aleatoric_variance=64.0,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["REGISTRY_2000_GAUCHER"]),
                uncertainty_source="Coulter impedance count variation"
            ),
            evidence_ids=["REGISTRY_2000_GAUCHER"],
            ordered=False,
            reported=False
        ))

        # 4. Hemoglobin
        hgb_val = float(np.round(np.clip(rng.normal(9.8, 0.7), 8.1, 11.4), 1))
        labs.append(LabMeasurement(
            measurement_id=f"lab_hgb_gd_m{current_month}",
            test_code="HEMOGLOBIN",
            test_name="Hemoglobin",
            category="Hematology",
            value=hgb_val,
            unit="g/dL",
            ref_low=12.0,
            ref_high=16.0,
            is_abnormal=(hgb_val < 12.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=hgb_val,
                ci_95_low=round(hgb_val - 1.96 * 0.4, 1),
                ci_95_high=round(hgb_val + 1.96 * 0.4, 1),
                aleatoric_variance=0.16,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["REGISTRY_2000_GAUCHER"]),
                uncertainty_source="Spectrophotometric cyanmethemoglobin assay error"
            ),
            evidence_ids=["REGISTRY_2000_GAUCHER"],
            ordered=False,
            reported=False
        ))

        return labs

    def generate_imaging_studies(
        self, current_month: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[ImagingStudy]:
        return [
            ImagingStudy(
                study_id="img_xray_femur_gd",
                modality="Bilateral Femur Digital Radiography (AP & Lateral)",
                anatomical_region="Bilateral Lower Extremity / Distal Femur",
                timestamp_month=current_month,
                acronym="XR-FEMUR",
                acr_findings=(
                    "Bilateral distal femoral metadiaphyseal flaring with loss of normal concavity, producing "
                    "the classical 'Erlenmeyer Flask Deformity'. Diffuse trabecular osteopenia and cortical thinning "
                    "consistent with medullary Gaucher cell infiltration. No acute cortical disruption or pathological fracture."
                ),
                radiology_impression=(
                    "1. Classical Erlenmeyer flask deformity of bilateral distal femurs.\n"
                    "2. Marked medullary osteopenia consistent with advanced marrow infiltration in lysosomal storage disorder."
                ),
                parametric_features=[
                    ImagingParametricFeature(
                        feature_name="Distal Femur Metaphyseal-Diaphyseal Flaring Ratio",
                        z_score=4.2,
                        quantitative_value=2.45,
                        unit="ratio",
                        attenuation_or_signal="Erlenmeyer Contour Flaring",
                        organ="Bilateral Distal Femurs"
                    )
                ],
                pathological_signs=["Erlenmeyer Flask Deformity", "Diffuse Medullary Osteopenia"],
                evidence_ids=["SEMINARS_2004_GAUCHER", "REGISTRY_2000_GAUCHER"],
                ordered=False,
                reported=False,
                schematic_data={
                    "type": "skeletal_femur_slice",
                    "erlenmeyer_flaring": True,
                    "trabecular_osteopenia": "marked"
                }
            ),
            ImagingStudy(
                study_id="img_us_abdomen_gd",
                modality="Abdominal Ultrasound / Visceral Volumetry",
                anatomical_region="Abdomen / Reticuloendothelial Organs",
                timestamp_month=current_month,
                acronym="US-VISCERAL",
                acr_findings=(
                    "Massive splenomegaly measuring 22.8 cm in craniocaudal length (estimated volume 1,650 cm3, ~12-fold normal). "
                    "Moderate hepatomegaly measuring 18.5 cm span. The splenic and hepatic parenchyma exhibit homogeneous, mildly "
                    "hyperechoic texture without focal discrete lesions."
                ),
                radiology_impression=(
                    "Massive splenomegaly (12x normal) and hepatomegaly without focal mass lesions, characteristic of severe "
                    "reticuloendothelial storage disorder."
                ),
                parametric_features=[
                    ImagingParametricFeature(
                        feature_name="Spleen Multiples of Normal Volume (MNV)",
                        z_score=5.6,
                        quantitative_value=12.2,
                        unit="multiples_of_normal",
                        attenuation_or_signal="Massive Homogeneous Enlargement",
                        organ="Spleen"
                    )
                ],
                pathological_signs=["Massive Splenomegaly (12x MNV)", "Hepatomegaly"],
                evidence_ids=["REGISTRY_2000_GAUCHER"],
                ordered=False,
                reported=False,
                schematic_data={
                    "type": "visceral_organ_slice",
                    "spleen_length_cm": 22.8,
                    "liver_length_cm": 18.5,
                    "splenomegaly_severity": "massive"
                }
            )
        ]

    def generate_encounter_notes(
        self, current_month: int, disease_stage: str, symptoms: List[ClinicalSymptom], rng: np.random.Generator
    ) -> List[ClinicalEncounterNote]:
        return [
            ClinicalEncounterNote(
                encounter_id=f"enc_gd_m{current_month}",
                timestamp_month=current_month,
                encounter_type="Hematology-Oncology Consultation",
                chief_complaint="Massive abdominal distension, spontaneous bleeding/bruising, and chronic skeletal bone pain.",
                hpi=(
                    "Patient referred for evaluation of progressive left-sided abdominal swelling and unexplained bicytopenia. "
                    "Reports profound fatigue, early fullness after a few bites of food, and recurrent epistaxis. "
                    "Past history is notable for recurrent deep aching in both thighs often misdiagnosed as growing pains or sports fatigue."
                ),
                physical_exam={
                    "General": "Pale, thin-limbed individual with disproportionately protuberant abdomen.",
                    "Abdomen": "Enormous firm spleen palpable crossing midline down into the left iliac fossa. Non-tender. Liver edge palpable 4 cm below costal margin.",
                    "Extremities": "Scattered purpuric macules on lower shins. Tenderness upon palpation of distal femoral metaphyses."
                },
                assessment_and_plan=(
                    "Severe splenomegaly, bicytopenia, and skeletal complaints. Primary considerations include Gaucher disease, "
                    "Niemann-Pick disease, or myeloproliferative neoplasm. "
                    "Plan: Leukocyte beta-glucosidase assay, plasma lyso-Gb1 biomarker, bilateral femur radiographs, and abdominal imaging."
                ),
                disease_stage=disease_stage
            )
        ]

    def generate_treatment_scenarios(
        self, current_month: int, disease_stage: str, phenotype: str
    ) -> List[TreatmentResponseScenario]:
        return [
            TreatmentResponseScenario(
                scenario_id="gd_scen_ert_prompt",
                name="Enzyme Replacement Therapy (Imiglucerase 60 U/kg IV every 2 weeks)",
                intervention_type="Targeted Therapy",
                description="High-dose macrophage-targeted recombinant glucocerebrosidase every 2 weeks.",
                evidence_ids=["SEMINARS_2004_GAUCHER", "REGISTRY_2000_GAUCHER"],
                trajectory=[
                    CounterfactualTrajectoryPoint(
                        month=current_month, state_score=0.80, primary_biomarker_value=125.0, clinical_status="Baseline: Severe thrombocytopenia (68k), massive spleen (12x MNV)", ci_low=105.0, ci_high=145.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 3, state_score=0.62, primary_biomarker_value=65.0, clinical_status="Month 3: Platelets rise to 105k; early reduction in splenic engorgement", ci_low=55.0, ci_high=75.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 6, state_score=0.44, primary_biomarker_value=32.0, clinical_status="Month 6: Normalization of hemoglobin; spleen reduced by 35%; cessation of bone pain", ci_low=25.0, ci_high=39.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 12, state_score=0.25, primary_biomarker_value=14.0, clinical_status="Month 12: Near-complete visceral remission; platelets >150k; skeletal remineralization", ci_low=10.0, ci_high=18.0
                    )
                ],
                is_active=True
            )
        ]

    def get_physiological_constraints(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "GD_RULE_LYSO_GB1_ELEVATION",
                "name": "Plasma Lyso-Gb1 Elevation Bound",
                "category": "Physiological Range",
                "test_code": "LYSO_GB1",
                "min_value": 1.5,
                "severity": "FATAL_ERROR",
                "description": "Plasma Lyso-Gb1 must be elevated above normal threshold (>1.5 ng/mL) in symptomatic Gaucher disease."
            },
            {
                "rule_id": "GD_RULE_BETA_GLUCOSIDASE_DEFICIENCY",
                "name": "Beta-Glucosidase Deficiency Bound",
                "category": "Physiological Range",
                "test_code": "BETA_GLUCOSIDASE",
                "max_value": 2.5,
                "severity": "FATAL_ERROR",
                "description": "Leukocyte beta-glucosidase activity in affected patients must be subnormal (<2.5 nmol/h/mg)."
            }
        ]
