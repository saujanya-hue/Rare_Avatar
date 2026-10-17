"""Clinical Mystery Mode Engine.

Manages interactive diagnostic challenges with multi-tier difficulty levels,
strict blinding, investigation cost & turnaround modeling, and educational debriefing.
"""
import uuid
import random
import datetime
from typing import Dict, List, Tuple, Optional, Any

from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.mystery import (
    MysterySessionConfig, MysteryCaseView, MysteryInvestigationItem,
    MysteryInvestigationOrderRequest, MysteryInquiryRequest,
    MysterySubmissionRequest, MysteryScorecard, EducationalDebriefing,
    MysteryDebriefingReport
)
from app.generators.patient_generator import patient_generator
from app.disease_models import disease_registry
from app.knowledge.evidence_base import evidence_base
from app.engine.dialogue_manager import dialogue_manager


INVESTIGATION_PRICE_CATALOG = {
    # Wilson Tests
    "CERULOPLASMIN": {"cost": 65.0, "hours": 4.0, "name": "Serum Ceruloplasmin"},
    "URINARY_COPPER_24H": {"cost": 120.0, "hours": 24.0, "name": "24-Hour Urinary Copper"},
    "AST": {"cost": 35.0, "hours": 2.0, "name": "Aspartate Aminotransferase (AST)"},
    "ALT": {"cost": 35.0, "hours": 2.0, "name": "Alanine Aminotransferase (ALT)"},
    "TOTAL_BILIRUBIN": {"cost": 30.0, "hours": 2.0, "name": "Total Bilirubin"},
    "PLATELETS": {"cost": 25.0, "hours": 1.5, "name": "Complete Blood Count (Platelets)"},
    "MRI-BRAIN": {"cost": 850.0, "hours": 12.0, "name": "Brain MRI (T1/T2/FLAIR)"},
    "SLIT-LAMP": {"cost": 180.0, "hours": 2.0, "name": "Slit-Lamp Ophthalmic Exam (KF Rings)"},

    # Fabry Tests
    "LYSO_GB3": {"cost": 290.0, "hours": 48.0, "name": "Plasma Lyso-Gb3 Biomarker (LC-MS/MS)"},
    "ALPHA_GALACTOSIDASE_A": {"cost": 220.0, "hours": 36.0, "name": "Leukocyte Alpha-Galactosidase A Activity"},
    "URINE_PROTEIN_24H": {"cost": 50.0, "hours": 24.0, "name": "24-Hour Urine Protein"},
    "ECHO-CARDIAC": {"cost": 550.0, "hours": 4.0, "name": "Transthoracic Echocardiogram (LVH)"},

    # Gaucher Tests
    "LYSO_GB1": {"cost": 310.0, "hours": 48.0, "name": "Plasma Glucosylsphingosine (Lyso-Gb1)"},
    "BETA_GLUCOSIDASE": {"cost": 240.0, "hours": 36.0, "name": "Leukocyte Acid Beta-Glucosidase Activity"},
    "HEMOGLOBIN": {"cost": 25.0, "hours": 1.5, "name": "Hemoglobin & Hematocrit"},
    "US-VISCERAL": {"cost": 380.0, "hours": 3.0, "name": "Visceral Abdominal Ultrasound (Spleen/Liver Vol)"},
    "XR-SKELETAL": {"cost": 220.0, "hours": 2.0, "name": "Bilateral Femur Radiography (Erlenmeyer Flask)"}
}


class MysteryManager:
    def __init__(self):
        # Maps session_id -> { "config": MysterySessionConfig, "patient": SyntheticPatientSpecification, "view": MysteryCaseView, "inquiry_count": int }
        self._sessions: Dict[str, Dict[str, Any]] = {}
        # Completed reports for supervisor review
        self._completed_reports: List[MysteryDebriefingReport] = []

    def start_session(self, config: MysterySessionConfig) -> MysteryCaseView:
        session_id = f"MYS-{uuid.uuid4().hex[:8].upper()}"
        started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Resolve Target Disease
        if config.disease_selection == "random" or config.disease_selection not in disease_registry:
            d_id = random.choice(["wilson_disease", "fabry_disease", "gaucher_disease"])
        else:
            d_id = config.disease_selection

        seed = config.random_seed if config.random_seed is not None else random.randint(1000, 99999)

        # 2. Generate Synthetic Patient Avatar
        patient = patient_generator.generate_patient(disease_id=d_id, seed=seed)

        # 3. Assemble Blinded Trainee View based on Difficulty Level
        chief_complaint = self._formulate_chief_complaint(patient, config.difficulty)

        # In beginner mode, reveal 2 core initial symptoms; in intermediate 1; in advanced only chief complaint
        if config.difficulty == "beginner":
            init_symptoms = patient.symptoms[:2]
        elif config.difficulty == "intermediate":
            init_symptoms = patient.symptoms[:1]
        else:  # advanced
            init_symptoms = []

        view = MysteryCaseView(
            session_id=session_id,
            trainee_id=config.trainee_id,
            difficulty=config.difficulty,
            patient_id=patient.patient_id,
            age_years=patient.demographics.age_years,
            biological_sex=patient.demographics.biological_sex,
            ethnicity=patient.demographics.ethnicity,
            chief_complaint=chief_complaint,
            available_symptoms=init_symptoms,
            ordered_investigations=[],
            accumulated_cost_usd=0.0,
            accumulated_turnaround_hours=0.0,
            status="IN_PROGRESS",
            started_at=started_at
        )

        self._sessions[session_id] = {
            "config": config,
            "patient": patient,
            "view": view,
            "inquiry_count": 0
        }

        return view

    def process_inquiry(self, req: MysteryInquiryRequest) -> Dict[str, Any]:
        session_data = self._sessions.get(req.session_id)
        if not session_data:
            raise ValueError(f"Mystery session '{req.session_id}' not found.")

        session_data["inquiry_count"] += 1
        patient: SyntheticPatientSpecification = session_data["patient"]

        resp = dialogue_manager.process_inquiry(
            patient=patient,
            query_text=req.query_text
        )

        # If inquiry revealed new symptoms, add them to available symptoms in the view
        if resp.revealed_findings:
            current_symp_names = {s.name.lower() for s in session_data["view"].available_symptoms}
            for rf in resp.revealed_findings:
                match = next((s for s in patient.symptoms if s.name.lower() == rf.lower()), None)
                if match and match.name.lower() not in current_symp_names:
                    session_data["view"].available_symptoms.append(match)

        return {
            "session_id": req.session_id,
            "avatar_response": resp.avatar_response,
            "revealed_findings": resp.revealed_findings,
            "simulation_month": resp.simulation_month
        }

    def order_investigation(self, req: MysteryInvestigationOrderRequest) -> MysteryInvestigationItem:
        session_data = self._sessions.get(req.session_id)
        if not session_data:
            raise ValueError(f"Mystery session '{req.session_id}' not found.")

        view: MysteryCaseView = session_data["view"]
        patient: SyntheticPatientSpecification = session_data["patient"]
        code_upper = req.code_or_acronym.upper()

        pricing = INVESTIGATION_PRICE_CATALOG.get(code_upper, {"cost": 95.0, "hours": 6.0, "name": req.code_or_acronym})
        cost = pricing["cost"]
        hours = pricing["hours"]
        name = pricing["name"]

        # Check if lab test
        result_str = "Within Normal Limits."
        is_abn = False

        if req.investigation_type == "lab":
            lab = next((l for l in patient.lab_history if l.test_code.upper() == code_upper), None)
            if lab:
                result_str = f"{lab.value} {lab.unit} (Ref: {lab.ref_low} - {lab.ref_high} {lab.unit}). {'ABNORMAL' if lab.is_abnormal else 'NORMAL'}"
                is_abn = lab.is_abnormal
            else:
                result_str = "Test performed: Non-reactive / within normal physiological reference range."

        else:  # imaging
            img = next((i for i in patient.imaging_studies if getattr(i, "acronym", "").upper() == code_upper or code_upper in i.study_id.upper()), None)
            if img:
                result_str = f"{img.radiology_impression} Findings: {img.acr_findings}"
                is_abn = len(getattr(img, "pathological_signs", [])) > 0
            else:
                result_str = "Study reviewed: No acute focal pathology or structural abnormalities detected."

        inv_item = MysteryInvestigationItem(
            investigation_id=f"INV-{uuid.uuid4().hex[:6].upper()}",
            modality=req.investigation_type.upper(),
            code_or_acronym=code_upper,
            name=name,
            simulated_cost_usd=cost,
            turnaround_hours=hours,
            result_summary=result_str,
            is_abnormal=is_abn,
            timestamp_ordered=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

        view.ordered_investigations.append(inv_item)
        view.accumulated_cost_usd += cost
        view.accumulated_turnaround_hours += hours

        return inv_item

    def submit_diagnosis(self, submission: MysterySubmissionRequest) -> MysteryDebriefingReport:
        session_data = self._sessions.get(submission.session_id)
        if not session_data:
            raise ValueError(f"Mystery session '{submission.session_id}' not found.")

        patient: SyntheticPatientSpecification = session_data["patient"]
        view: MysteryCaseView = session_data["view"]
        cfg: MysterySessionConfig = session_data["config"]

        gt_id = patient.disease.disease_id
        gt_name = patient.disease.disease_name
        pred_id = submission.predicted_disease_id.lower().strip()

        # 1. Scoring
        is_top1 = (pred_id == gt_id)
        top3_ids = [list(d.keys())[0].lower() for d in submission.differential_diagnoses[:3]]
        is_top3 = is_top1 or any(gt_id in name for name in top3_ids)

        accuracy_score = 100.0 if is_top1 else (65.0 if is_top3 else 15.0)

        # Cost efficiency: budget threshold $900
        budget = 1100.0 if cfg.difficulty == "beginner" else (850.0 if cfg.difficulty == "intermediate" else 650.0)
        cost_ratio = view.accumulated_cost_usd / max(100.0, budget)
        cost_score = max(20.0, min(100.0, 100.0 - max(0.0, (cost_ratio - 1.0) * 80.0)))

        # Parsimony score: penalty for ordering unrelated high-cost tests
        investigations_count = len(view.ordered_investigations)
        parsimony_score = max(30.0, min(100.0, 100.0 - max(0, investigations_count - 5) * 12.0))

        overall_score = round(0.55 * accuracy_score + 0.25 * cost_score + 0.20 * parsimony_score, 1)

        if overall_score >= 88.0:
            band = "EXEMPLARY (HONORS)"
        elif overall_score >= 72.0:
            band = "PROFICIENT"
        elif overall_score >= 55.0:
            band = "MARGINAL"
        else:
            band = "NEEDS_REMEDIATION"

        scorecard = MysteryScorecard(
            is_top1_correct=is_top1,
            is_top3_correct=is_top3,
            accuracy_score=accuracy_score,
            cost_efficiency_score=round(cost_score, 1),
            diagnostic_parsimony_score=round(parsimony_score, 1),
            overall_clinical_score=overall_score,
            performance_band=band
        )

        # 2. Educational Debriefing
        debriefing = self._build_educational_debriefing(patient, submission, is_top1)

        report = MysteryDebriefingReport(
            session_id=submission.session_id,
            trainee_id=view.trainee_id,
            difficulty=view.difficulty,
            ground_truth_disease_id=gt_id,
            ground_truth_disease_name=gt_name,
            submission=submission,
            scorecard=scorecard,
            total_cost_usd=round(view.accumulated_cost_usd, 2),
            total_turnaround_hours=round(view.accumulated_turnaround_hours, 1),
            investigations_count=investigations_count,
            inquiries_count=session_data["inquiry_count"],
            debriefing=debriefing,
            completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

        view.status = "SUBMITTED"
        self._completed_reports.append(report)
        return report

    def list_supervisor_sessions(self) -> List[MysteryDebriefingReport]:
        return self._completed_reports

    def get_session_view(self, session_id: str) -> Optional[MysteryCaseView]:
        if session_id in self._sessions:
            return self._sessions[session_id]["view"]
        return None

    def _formulate_chief_complaint(self, patient: SyntheticPatientSpecification, difficulty: str) -> str:
        d_id = patient.disease.disease_id
        if d_id == "wilson_disease":
            if difficulty == "beginner":
                return "22-year-old presenting with progressive bilateral hand tremors, subtle speech slurring, and recurrent unexplained jaundice."
            elif difficulty == "intermediate":
                return "26-year-old referred for persistent mild transaminitis, emotional lability, and declining fine motor handwriting coordination."
            else:
                return "34-year-old evaluated for atypical fatigue, vague right upper quadrant fullness, and low-grade acute-phase inflammatory markers."

        elif d_id == "fabry_disease":
            if difficulty == "beginner":
                return "19-year-old presenting with episodic burning pain in hands and feet exacerbated by exercise and heat, with dark punctate skin lesions."
            elif difficulty == "intermediate":
                return "28-year-old with bilateral neuropathic extremity burning, heat intolerance, and borderline microalbuminuria on routine urinalysis."
            else:
                return "38-year-old presenting with non-specific exercise dyspnea, mild concentric left ventricular wall thickening, and chronic acral paresthesias."

        else:  # Gaucher
            if difficulty == "beginner":
                return "24-year-old presenting with massive abdominal enlargement, recurrent epistaxis, severe easy bruising, and deep aching thigh pain."
            elif difficulty == "intermediate":
                return "29-year-old with progressive fatigue, marked left upper quadrant splenic fullness, and profound isolated thrombocytopenia."
            else:
                return "42-year-old evaluated for intermittent skeletal bone aches, mild chronic microcytic anemia, and splenomegaly discovered on physical exam."

    def _build_educational_debriefing(
        self, patient: SyntheticPatientSpecification, submission: MysterySubmissionRequest, is_correct: bool
    ) -> EducationalDebriefing:
        d_id = patient.disease.disease_id
        refs = evidence_base.get_evidence_by_disease(d_id)

        if d_id == "wilson_disease":
            findings = [
                "Serum ceruloplasmin < 20 mg/dL (ATP7B impaired holoceruloplasmin incorporation)",
                "24-hour urinary copper excretion > 100 ug/24h (systemic copper overflow cupriuresis)",
                "Slit-lamp Kayser-Fleischer rings (Descemet's membrane copper deposition)",
                "Brainstem MRI 'Face of the Giant Panda' midbrain T2 hyperintensity"
            ]
            pitfalls = [
                "Anchoring on isolated elevated transaminases as non-specific viral hepatitis or autoimmune hepatitis",
                "Failing to perform a slit-lamp ophthalmic examination in young adults with unexplained neuropsychiatric symptoms",
                "Assuming normal ceruloplasmin rules out Wilson disease (it can be an acute-phase reactant in active acute liver failure)"
            ]
            takeaway = "In young patients presenting with concurrent hepatic injury and neuropsychiatric symptoms, always calculate the Leipzig Diagnostic Score and obtain 24h urinary copper."

        elif d_id == "fabry_disease":
            findings = [
                "Elevated plasma globotriaosylsphingosine (Lyso-Gb3 > 0.8 ng/mL)",
                "Subnormal leukocyte alpha-galactosidase A enzyme activity (< 4.0 nmol/h/mg)",
                "Neuropathic acroparesthesias triggered by thermal stress or febrile illness",
                "Concentric left ventricular hypertrophy with disproportionate native T1 myocardial shortening"
            ]
            pitfalls = [
                "Misdiagnosing burning extremity pain as juvenile idiopathic arthritis, fibromyalgia, or growing pains",
                "Overlooking cutaneous angiokeratomas in the 'bathing trunk' distribution",
                "Attributing left ventricular hypertrophy to essential hypertension without considering storage cardiomyopathy"
            ]
            takeaway = "Unexplained small fiber neuropathy in youth coupled with early microalbuminuria and cardiac hypertrophy should trigger immediate Lyso-Gb3 and Alpha-Gal A screening."

        else:  # Gaucher
            findings = [
                "Massive splenomegaly (frequently 5x to 20x normal volume) from sinusoidal Gaucher cell infiltration",
                "Peripheral cytopenias (especially severe thrombocytopenia < 100,000/uL and anemia)",
                "Markedly elevated plasma Lyso-Gb1 (glucosylsphingosine > 1.5 ng/mL)",
                "Erlenmeyer flask distal femoral deformity on skeletal radiography"
            ]
            pitfalls = [
                "Misattributing splenomegaly and thrombocytopenia to primary hematologic malignancies (e.g. leukemia/lymphoma) before enzyme testing",
                "Ordering invasive bone marrow biopsy when non-invasive beta-glucosidase and Lyso-Gb1 assays are diagnostic",
                "Dismissing bone crisis pain as osteomyelitis or growing pains"
            ]
            takeaway = "The combination of hypersplenomegaly and thrombocytopenia in the absence of portal hypertension strongly points to Gaucher disease Type 1, readily confirmed by leukocyte beta-glucosidase assay."

        return EducationalDebriefing(
            correct_disease_name=patient.disease.disease_name,
            omim_id=patient.disease.omim_id,
            phenotype_summary=f"Synthetic Avatar {patient.patient_id} modeled with canonical {patient.disease.disease_name} pathophysiology.",
            pathognomonic_findings=findings,
            common_pitfalls_avoided_or_committed=pitfalls,
            relevant_guidelines=refs,
            clinical_takeaway=takeaway
        )


mystery_manager = MysteryManager()
