"""Wilson Disease Pathophysiological Model (OMIM: 277900, Orpha: 905)."""
import numpy as np
from typing import List, Dict, Any
from app.disease_models.base import BaseDiseaseModel
from app.schemas.patient import (
    DiseaseMetadata, ClinicalSymptom, LabMeasurement, ImagingStudy,
    ImagingParametricFeature, ClinicalEncounterNote, TreatmentResponseScenario,
    CounterfactualTrajectoryPoint, UncertaintyBounds
)
from app.knowledge.evidence_base import evidence_base


class WilsonDiseaseModel(BaseDiseaseModel):
    @property
    def disease_id(self) -> str:
        return "wilson_disease"

    @property
    def metadata(self) -> DiseaseMetadata:
        return DiseaseMetadata(
            disease_id="wilson_disease",
            disease_name="Wilson Disease (Hepatolenticular Degeneration)",
            omim_id="#277900",
            orpha_code="ORPHA:905",
            genetic_basis="Autosomal recessive mutations in the ATP7B gene (copper-transporting P-type ATPase) on chromosome 13q14.3",
            prevalence="Estimated 1 in 30,000 live births",
            inheritance="Autosomal Recessive"
        )

    @property
    def supported_phenotypes(self) -> List[str]:
        return ["Hepatic Predominant", "Neurologic Predominant", "Mixed Hepato-Neurological"]

    @property
    def evidence_keys(self) -> List[str]:
        return ["EASL_2012_GUIDELINES", "LANCET_2015_WILSON", "FERENCI_2003_CLASSIF"]

    def generate_symptoms(
        self, age_years: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[ClinicalSymptom]:
        symptoms = []
        is_neuro = phenotype in ["Neurologic Predominant", "Mixed Hepato-Neurological"]
        is_hepatic = phenotype in ["Hepatic Predominant", "Mixed Hepato-Neurological"]

        # Universal constitutional / early symptom
        symptoms.append(ClinicalSymptom(
            symptom_id="wd_sym_fatigue",
            name="Chronic Unexplained Fatigue and Lethargy",
            category="Constitutional",
            onset_month=max(1, int(rng.integers(2, 6))),
            severity_score=float(np.round(rng.uniform(4.0, 7.5), 1)),
            description="Persistent generalized fatigue not alleviated by rest, accompanied by mild malaise.",
            is_revealed=True,
            evidence_ids=["EASL_2012_GUIDELINES", "LANCET_2015_WILSON"]
        ))

        if is_hepatic:
            symptoms.append(ClinicalSymptom(
                symptom_id="wd_sym_jaundice",
                name="Scleral Icterus and Episodic Jaundice",
                category="Hepatic",
                onset_month=max(2, int(rng.integers(4, 9))),
                severity_score=float(np.round(rng.uniform(5.0, 8.5), 1)),
                description="Yellowish discoloration of sclera and skin with dark tea-colored urine.",
                is_revealed=True,
                evidence_ids=["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"]
            ))
            symptoms.append(ClinicalSymptom(
                symptom_id="wd_sym_ruq_pain",
                name="Right Upper Quadrant Abdominal Discomfort",
                category="Hepatic",
                onset_month=max(3, int(rng.integers(5, 11))),
                severity_score=float(np.round(rng.uniform(3.5, 6.0), 1)),
                description="Dull aching pressure beneath the right costal margin related to hepatomegaly.",
                is_revealed=False,
                evidence_ids=["EASL_2012_GUIDELINES"]
            ))

        if is_neuro:
            symptoms.append(ClinicalSymptom(
                symptom_id="wd_sym_tremor",
                name="Postural and Intention Tremor ('Wing-Beating')",
                category="Neurologic",
                onset_month=max(4, int(rng.integers(7, 14))),
                severity_score=float(np.round(rng.uniform(5.5, 9.0), 1)),
                description="Prominent tremor exacerbated by arm abduction and finger-to-nose targeting.",
                is_revealed=True,
                evidence_ids=["LANCET_2015_WILSON", "FERENCI_2003_CLASSIF"]
            ))
            symptoms.append(ClinicalSymptom(
                symptom_id="wd_sym_dysarthria",
                name="Progressive Slurred Speech (Dysarthria)",
                category="Neurologic",
                onset_month=max(5, int(rng.integers(8, 16))),
                severity_score=float(np.round(rng.uniform(4.0, 8.0), 1)),
                description="Staccato, scanning or spastic-ataxic speech with diminished vocal inflection.",
                is_revealed=False,
                evidence_ids=["LANCET_2015_WILSON"]
            ))
            symptoms.append(ClinicalSymptom(
                symptom_id="wd_sym_dystonia",
                name="Facial Grimacing and Pseudobulbar Affect",
                category="Neuropsychiatric",
                onset_month=max(6, int(rng.integers(10, 18))),
                severity_score=float(np.round(rng.uniform(3.0, 7.0), 1)),
                description="Involuntary risus sardonicus smile, increased emotional lability and mood irritability.",
                is_revealed=False,
                evidence_ids=["LANCET_2015_WILSON"]
            ))

        return symptoms

    def generate_laboratory_trajectories(
        self, current_month: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[LabMeasurement]:
        labs = []

        # 1. Serum Ceruloplasmin (Markedly reduced in ~90% of WD)
        cp_mean = 7.5 if disease_stage != "Early Pre-Symptomatic" else 14.0
        cp_val = float(np.round(np.clip(rng.normal(cp_mean, 1.8), 2.0, 16.0), 1))
        labs.append(LabMeasurement(
            measurement_id=f"lab_cp_m{current_month}",
            test_code="CERULOPLASMIN",
            test_name="Serum Ceruloplasmin",
            category="Copper Metabolism",
            value=cp_val,
            unit="mg/dL",
            ref_low=20.0,
            ref_high=40.0,
            is_abnormal=(cp_val < 20.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=cp_val,
                ci_95_low=round(cp_val - 1.96 * 1.8, 1),
                ci_95_high=round(cp_val + 1.96 * 1.8, 1),
                aleatoric_variance=1.8 ** 2,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"]),
                uncertainty_source="Analytical nephelometry immunoassay precision & biological copper turnover"
            ),
            evidence_ids=["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"],
            ordered=False,
            reported=False
        ))

        # 2. 24-Hour Urinary Copper (Markedly elevated)
        ucu_mean = 185.0 if disease_stage == "Decompensated/Advanced" else 135.0
        ucu_val = float(np.round(np.clip(rng.normal(ucu_mean, 25.0), 75.0, 380.0), 1))
        labs.append(LabMeasurement(
            measurement_id=f"lab_ucu_m{current_month}",
            test_code="URINARY_COPPER_24H",
            test_name="24-Hour Urinary Copper Excretion",
            category="Copper Metabolism",
            value=ucu_val,
            unit="ug/24h",
            ref_low=15.0,
            ref_high=50.0,
            is_abnormal=(ucu_val > 50.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=ucu_val,
                ci_95_low=round(ucu_val - 1.96 * 25.0, 1),
                ci_95_high=round(ucu_val + 1.96 * 25.0, 1),
                aleatoric_variance=25.0 ** 2,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"]),
                uncertainty_source="Diurnal urinary copper fluctuation & collection completeness variance"
            ),
            evidence_ids=["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"],
            ordered=False,
            reported=False
        ))

        # 3. Serum AST
        ast_val = float(np.round(np.clip(rng.normal(145.0, 30.0), 65.0, 310.0), 1))
        labs.append(LabMeasurement(
            measurement_id=f"lab_ast_m{current_month}",
            test_code="AST",
            test_name="Aspartate Aminotransferase (AST)",
            category="Hepatic Panel",
            value=ast_val,
            unit="U/L",
            ref_low=10.0,
            ref_high=40.0,
            is_abnormal=(ast_val > 40.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=ast_val,
                ci_95_low=round(ast_val - 1.96 * 15.0, 1),
                ci_95_high=round(ast_val + 1.96 * 15.0, 1),
                aleatoric_variance=15.0 ** 2,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["EASL_2012_GUIDELINES"]),
                uncertainty_source="Enzymatic rate photometric assay variance"
            ),
            evidence_ids=["EASL_2012_GUIDELINES"],
            ordered=False,
            reported=False
        ))

        # 4. Serum ALT
        alt_val = float(np.round(np.clip(rng.normal(120.0, 25.0), 55.0, 280.0), 1))
        labs.append(LabMeasurement(
            measurement_id=f"lab_alt_m{current_month}",
            test_code="ALT",
            test_name="Alanine Aminotransferase (ALT)",
            category="Hepatic Panel",
            value=alt_val,
            unit="U/L",
            ref_low=7.0,
            ref_high=56.0,
            is_abnormal=(alt_val > 56.0),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=alt_val,
                ci_95_low=round(alt_val - 1.96 * 14.0, 1),
                ci_95_high=round(alt_val + 1.96 * 14.0, 1),
                aleatoric_variance=14.0 ** 2,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["EASL_2012_GUIDELINES"]),
                uncertainty_source="Enzymatic rate photometric assay variance"
            ),
            evidence_ids=["EASL_2012_GUIDELINES"],
            ordered=False,
            reported=False
        ))

        # 5. Total Bilirubin
        bili_val = float(np.round(np.clip(rng.normal(2.6, 0.6), 1.2, 5.8), 2))
        labs.append(LabMeasurement(
            measurement_id=f"lab_tbili_m{current_month}",
            test_code="TOTAL_BILIRUBIN",
            test_name="Total Serum Bilirubin",
            category="Hepatic Panel",
            value=bili_val,
            unit="mg/dL",
            ref_low=0.2,
            ref_high=1.2,
            is_abnormal=(bili_val > 1.2),
            timestamp_month=current_month,
            uncertainty=UncertaintyBounds(
                point_estimate=bili_val,
                ci_95_low=round(bili_val - 1.96 * 0.3, 2),
                ci_95_high=round(bili_val + 1.96 * 0.3, 2),
                aleatoric_variance=0.09,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["EASL_2012_GUIDELINES"]),
                uncertainty_source="Spectrophotometric diazo coupling variance"
            ),
            evidence_ids=["EASL_2012_GUIDELINES"],
            ordered=False,
            reported=False
        ))

        # 6. Platelet Count
        plt_val = float(np.round(np.clip(rng.normal(128.0, 18.0), 80.0, 220.0), 0))
        labs.append(LabMeasurement(
            measurement_id=f"lab_plt_m{current_month}",
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
                ci_95_low=round(plt_val - 1.96 * 10.0, 0),
                ci_95_high=round(plt_val + 1.96 * 10.0, 0),
                aleatoric_variance=100.0,
                epistemic_confidence_score=evidence_base.compute_epistemic_confidence(["FERENCI_2003_CLASSIF"]),
                uncertainty_source="Automated impedance cell counter precision"
            ),
            evidence_ids=["FERENCI_2003_CLASSIF"],
            ordered=False,
            reported=False
        ))

        return labs

    def generate_imaging_studies(
        self, current_month: int, disease_stage: str, phenotype: str, rng: np.random.Generator
    ) -> List[ImagingStudy]:
        studies = []

        # 1. Brain MRI (T2/FLAIR)
        studies.append(ImagingStudy(
            study_id="img_mri_brain_wd",
            modality="Brain MRI (T1, T2, FLAIR, DWI)",
            anatomical_region="Central Nervous System / Brainstem & Basal Ganglia",
            timestamp_month=current_month,
            acronym="MRI-BRAIN",
            acr_findings=(
                "Bilateral, symmetrical high signal intensity on T2-weighted and FLAIR sequences involving "
                "the putamen, globus pallidus, and caudate nuclei. Characteristic high signal intensity in the "
                "midbrain tegmentum with preserved normal hypointensity of the red nuclei and substantia nigra, "
                "producing the classic 'Face of the Giant Panda' sign. No acute intracranial hemorrhage or mass effect."
            ),
            radiology_impression=(
                "1. Symmetrical bilateral deep gray matter and brainstem signal alterations consistent with toxic "
                "metal deposition, highly characteristic of Wilson disease.\n"
                "2. Midbrain 'Face of Giant Panda' configuration confirms advanced neurological copper overload."
            ),
            parametric_features=[
                ImagingParametricFeature(
                    feature_name="Midbrain Tegmentum T2/FLAIR Hyperintensity Ratio",
                    z_score=3.4,
                    quantitative_value=1.85,
                    unit="signal_ratio_to_thalamus",
                    attenuation_or_signal="Hyperintense",
                    organ="Brainstem (Midbrain)"
                ),
                ImagingParametricFeature(
                    feature_name="Lentiform Nucleus Bilateral Volume Loss Z-Score",
                    z_score=-2.3,
                    quantitative_value=-2.3,
                    unit="z_score",
                    attenuation_or_signal="Iso/Hyperintense T2",
                    organ="Basal Ganglia"
                )
            ],
            pathological_signs=["Face of Giant Panda Sign", "Bilateral Putaminal T2 Hyperintensity"],
            evidence_ids=["LANCET_2015_WILSON", "FERENCI_2003_CLASSIF"],
            ordered=False,
            reported=False,
            schematic_data={
                "type": "brainstem_slice",
                "midbrain_width": 200,
                "red_nuclei_hypointense": True,
                "tegmentum_hyperintense": True,
                "panda_sign_present": True
            }
        ))

        # 2. Slit-Lamp Biomicroscopy
        studies.append(ImagingStudy(
            study_id="img_slit_lamp_wd",
            modality="Slit-Lamp Ophthalmic Biomicroscopy",
            anatomical_region="Anterior Segment / Cornea",
            timestamp_month=current_month,
            acronym="SLIT-LAMP",
            acr_findings=(
                "Bilateral golden-brown granular pigment deposition at the limbic periphery of the cornea "
                "within Descemet's membrane (Kayser-Fleischer rings). Ring extends 360 degrees circumferentially, "
                "most prominent superiorly and inferiorly. Anterior chamber is deep and quiet. Lenses clear."
            ),
            radiology_impression=(
                "Bilateral classical Kayser-Fleischer (KF) rings confirmed on slit lamp examination. "
                "In presence of neurological/hepatic manifestations, pathognomonic of copper storage disease."
            ),
            parametric_features=[
                ImagingParametricFeature(
                    feature_name="Descemet Membrane Copper Band Width",
                    z_score=4.1,
                    quantitative_value=1.4,
                    unit="mm",
                    attenuation_or_signal="Golden-Brown Granular Deposition",
                    organ="Corneal Periphery"
                )
            ],
            pathological_signs=["Kayser-Fleischer Rings"],
            evidence_ids=["EASL_2012_GUIDELINES", "LANCET_2015_WILSON"],
            ordered=False,
            reported=False,
            schematic_data={
                "type": "cornea_ring_slice",
                "ring_color": "#b8860b",
                "coverage_degrees": 360,
                "prominence": "high"
            }
        ))

        # 3. Abdominal Ultrasound
        studies.append(ImagingStudy(
            study_id="img_us_abdomen_wd",
            modality="High-Resolution Abdominal Ultrasound",
            anatomical_region="Hepatobiliary & Spleen",
            timestamp_month=current_month,
            acronym="US-ABDOMEN",
            acr_findings=(
                "The liver demonstrates a coarse, heterogeneous parenchymal echotexture with micronodular surface "
                "scalloping. Moderate hepatomegaly measuring 16.2 cm in craniocaudal dimension. The spleen is enlarged, "
                "measuring 14.5 cm in length (splenomegaly), consistent with portal hypertension. No focal liver masses "
                "or gallstones. Portal vein diameter is prominent at 13 mm with hepatopetal flow."
            ),
            radiology_impression=(
                "1. Micronodular cirrhotic architecture and hepatomegaly.\n"
                "2. Splenomegaly with signs of mild portal hypertensive venous congestion."
            ),
            parametric_features=[
                ImagingParametricFeature(
                    feature_name="Spleen Bipolar Length",
                    z_score=2.8,
                    quantitative_value=14.5,
                    unit="cm",
                    attenuation_or_signal="Homogeneous Enlargement",
                    organ="Spleen"
                ),
                ImagingParametricFeature(
                    feature_name="Liver Craniocaudal Span",
                    z_score=2.1,
                    quantitative_value=16.2,
                    unit="cm",
                    attenuation_or_signal="Coarse Parenchymal Texture",
                    organ="Liver"
                )
            ],
            pathological_signs=["Micronodular Liver Contour", "Splenomegaly", "Coarse Hepatic Echotexture"],
            evidence_ids=["EASL_2012_GUIDELINES"],
            ordered=False,
            reported=False,
            schematic_data={
                "type": "abdominal_ultrasound_slice",
                "liver_span_cm": 16.2,
                "spleen_span_cm": 14.5,
                "surface_nodularity": "moderate"
            }
        ))

        return studies

    def generate_encounter_notes(
        self, current_month: int, disease_stage: str, symptoms: List[ClinicalSymptom], rng: np.random.Generator
    ) -> List[ClinicalEncounterNote]:
        active_sym_desc = ", ".join([s.name for s in symptoms if s.is_revealed])
        return [
            ClinicalEncounterNote(
                encounter_id=f"enc_wd_m{current_month}",
                timestamp_month=current_month,
                encounter_type="Initial Diagnostic Assessment",
                chief_complaint=f"Patient presents with subacute worsening of {active_sym_desc.lower()}.",
                hpi=(
                    f"A previously healthy adult presents for evaluation of progressive decline over the past several months. "
                    f"The patient reports severe unexplained fatigue and noticeable hand tremor that interferes with writing and daily tasks. "
                    f"Family members report subtle personality changes and occasional slurring of speech over the last 12 weeks. "
                    f"No history of heavy alcohol consumption, viral hepatitis exposures, or prescription neuroleptics."
                ),
                physical_exam={
                    "General": "Alert, mildly fatigued appearing, cooperative.",
                    "HEENT": "Mild bilateral scleral icterus. Questionable dark ring visible at the superior limbic margins of the corneas.",
                    "Abdomen": "Soft, palpable liver edge 2 cm below right costal margin with mild tenderness. Splenomegaly noted on percussion.",
                    "Neurological": "Bilateral postural tremor of hands, exaggerated on intention testing. Mild dysarthria with scanning speech cadence. Muscle tone mildly increased in upper extremities (rigidity without spastic catch)."
                },
                assessment_and_plan=(
                    "Young adult presenting with dual hepatic and movement disorder symptoms without obvious toxic etiology. "
                    "Differential diagnosis includes: Wilson disease, juvenile hemochromatosis, autoimmune hepatitis, early-onset dystonia/Parkinsonism. "
                    "Plan: Diagnostic workup with ceruloplasmin, 24-hour urine copper, comprehensive liver panel, slit lamp exam, and brain MRI."
                ),
                disease_stage=disease_stage
            )
        ]

    def generate_treatment_scenarios(
        self, current_month: int, disease_stage: str, phenotype: str
    ) -> List[TreatmentResponseScenario]:
        return [
            TreatmentResponseScenario(
                scenario_id="wd_scen_chelation_prompt",
                name="First-Line Chelation Therapy (D-Penicillamine / Trientine)",
                intervention_type="Targeted Therapy",
                description=(
                    "Immediate initiation of copper chelating agent (D-Penicillamine 250mg qid gradually titrated, "
                    "or Trientine dihydrochloride) combined with Pyridoxine (vitamin B6). Promotes cupriuresis and halts cellular toxicity."
                ),
                evidence_ids=["EASL_2012_GUIDELINES", "LANCET_2015_WILSON"],
                trajectory=[
                    CounterfactualTrajectoryPoint(
                        month=current_month, state_score=0.75, primary_biomarker_value=185.0, clinical_status="Baseline: Active copper overload & hepatic/neurologic symptoms", ci_low=160.0, ci_high=210.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 3, state_score=0.62, primary_biomarker_value=620.0, clinical_status="Month 3: Marked cupriuresis (therapeutic urinary copper surge); transaminases stabilizing", ci_low=520.0, ci_high=720.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 6, state_score=0.45, primary_biomarker_value=240.0, clinical_status="Month 6: Liver function normalizes; neurologic tremor and dysarthria improving", ci_low=190.0, ci_high=290.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 12, state_score=0.22, primary_biomarker_value=75.0, clinical_status="Month 12: Stable maintenance phase; resolution of icterus, minimal residual tremor", ci_low=55.0, ci_high=95.0
                    )
                ],
                is_active=True
            ),
            TreatmentResponseScenario(
                scenario_id="wd_scen_delay_untreated",
                name="Delayed Diagnosis / Untreated Natural History",
                intervention_type="Untreated Natural History",
                description=(
                    "Failure to recognize copper overload leading to ongoing toxic accumulation in hepatic parenchymal cells "
                    "and basal ganglia neurons."
                ),
                evidence_ids=["EASL_2012_GUIDELINES", "FERENCI_2003_CLASSIF"],
                trajectory=[
                    CounterfactualTrajectoryPoint(
                        month=current_month, state_score=0.75, primary_biomarker_value=185.0, clinical_status="Baseline: Active symptomatic presentation", ci_low=160.0, ci_high=210.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 3, state_score=0.82, primary_biomarker_value=210.0, clinical_status="Month 3: Progressive dysarthria, emergence of severe fixed dystonic posturing", ci_low=180.0, ci_high=240.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 6, state_score=0.91, primary_biomarker_value=260.0, clinical_status="Month 6: Hepatic decompensation (ascites, coagulopathy INR > 2.0)", ci_low=220.0, ci_high=300.0
                    ),
                    CounterfactualTrajectoryPoint(
                        month=current_month + 12, state_score=0.98, primary_biomarker_value=320.0, clinical_status="Month 12: Acute-on-chronic liver failure / severe neurological disability requiring emergent transplant evaluation", ci_low=270.0, ci_high=370.0
                    )
                ],
                is_active=False
            )
        ]

    def get_physiological_constraints(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "WD_RULE_CERULOPLASMIN_UPPER_BOUND",
                "name": "Serum Ceruloplasmin Bound in Wilson Disease",
                "category": "Physiological Range",
                "test_code": "CERULOPLASMIN",
                "max_value": 20.0,
                "severity": "FATAL_ERROR",
                "description": "Ceruloplasmin in symptomatic classical Wilson disease should be < 20 mg/dL (ref 20-40 mg/dL)."
            },
            {
                "rule_id": "WD_RULE_URINARY_COPPER_LOWER_BOUND",
                "name": "24h Urinary Copper Elevation",
                "category": "Physiological Range",
                "test_code": "URINARY_COPPER_24H",
                "min_value": 50.0,
                "severity": "FATAL_ERROR",
                "description": "24-hour urinary copper excretion in active Wilson disease must exceed upper limit of normal (>50 ug/24h)."
            },
            {
                "rule_id": "WD_RULE_CROSS_MODAL_HEPATIC_CONGRUENCE",
                "name": "Transaminase and Hepatic Imaging Congruence",
                "category": "Cross-Modal Coherence",
                "severity": "WARNING",
                "description": "Marked AST/ALT elevation must correlate with abnormal liver echotexture on imaging."
            }
        ]
