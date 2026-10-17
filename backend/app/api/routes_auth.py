"""REST API routes for User Authentication, Role Verification, and Trainee Performance Tracking."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from app.schemas.auth import (
    LoginRequest, LoginResponse, UserProfile,
    TraineeDiagnosisSubmission, TraineeDiagnosisEvaluation
)
from app.engine.state_manager import state_manager

router = APIRouter(prefix="/api/auth", tags=["Authentication & Role Management"])

# In-memory storage for trainee submissions
_trainee_submissions_store: List[TraineeDiagnosisEvaluation] = []


def _seed_initial_trainee_records():
    """Seed initial trainee performance history so supervisor oversight is populated."""
    if _trainee_submissions_store:
        return
    now = datetime.now(timezone.utc).isoformat()
    _trainee_submissions_store.extend([
        TraineeDiagnosisEvaluation(
            submission_id="sub-tr-001",
            patient_id="SYNTH-WIL-00A411",
            trainee_id="TR-8041",
            trainee_email="TR-8041@ggmail.com",
            primary_diagnosis="Wilson Disease (ATP7B)",
            ground_truth_disease_id="wilson_disease",
            ground_truth_disease_name="Wilson Disease (Hepatolenticular Degeneration)",
            is_correct=True,
            accuracy_score=95.0,
            efficiency_score=88.0,
            hallmarks_detected=["Low Serum Ceruloplasmin", "Elevated 24h Urine Copper", "Postural Tremor"],
            missed_hallmarks=["Kayser-Fleischer Ring confirmation via slit-lamp"],
            supervisor_debriefing="Excellent diagnostic workup. Confirmed hepatic and neurological involvement with appropriate first-line ceruloplasmin screening.",
            submitted_at_utc=now
        ),
        TraineeDiagnosisEvaluation(
            submission_id="sub-tr-002",
            patient_id="SYNTH-FAB-00B522",
            trainee_id="TR-5120",
            trainee_email="TR-5120@ggmail.com",
            primary_diagnosis="Systemic Lupus Erythematosus",
            ground_truth_disease_id="fabry_disease",
            ground_truth_disease_name="Fabry Disease (Alpha-Galactosidase A Deficiency)",
            is_correct=False,
            accuracy_score=40.0,
            efficiency_score=62.0,
            hallmarks_detected=["Hypohidrosis", "Early neuropathic extremity pain"],
            missed_hallmarks=["Alpha-Galactosidase A leukocyte assay", "Plasma Lyso-Gb3 biomarker", "Angiokeratoma physical exam"],
            supervisor_debriefing="Diagnostic anchoring bias observed: confused episodic neuropathic acroparesthesias with autoimmune arthralgia. Recommend biochemical enzyme quantification.",
            submitted_at_utc=now
        ),
        TraineeDiagnosisEvaluation(
            submission_id="sub-tr-003",
            patient_id="SYNTH-GAU-00C633",
            trainee_id="TR-9042",
            trainee_email="TR-9042@ggmail.com",
            primary_diagnosis="Gaucher Disease Type 1 (Non-Neuronopathic)",
            ground_truth_disease_id="gaucher_disease",
            ground_truth_disease_name="Gaucher Disease Type 1",
            is_correct=True,
            accuracy_score=100.0,
            efficiency_score=92.0,
            hallmarks_detected=["Splenomegaly with Cytopenias", "Beta-Glucocerebrosidase Deficiency", "Bone pain / Erlenmeyer flask deformity"],
            missed_hallmarks=[],
            supervisor_debriefing="Outstanding differential deduction. Immediately recognized non-malignant massive splenomegaly with severe thrombocytopenia and ordered target enzyme assay.",
            submitted_at_utc=now
        )
    ])


_seed_initial_trainee_records()


@router.post("/login", response_model=LoginResponse)
def login_user(payload: LoginRequest):
    """
    Authenticate a user for either Trainee Mode or Supervisor Mode.
    
    Trainee requirement:
    - Login email must contain the Trainee ID followed by '@ggmail.com' (e.g. TR-8041@ggmail.com or trainee_id@ggmail.com).
    
    Supervisor requirement:
    - Login email can be e.g. SUP-001@ggmail.com or supervisor@ggmail.com.
    """
    raw_email = payload.email.strip().lower()
    selected_role = (payload.role or "").strip().lower()

    if not raw_email:
        raise HTTPException(status_code=400, detail="Email is required to access the medical portal.")

    # Determine role if explicitly selected or infer from email
    if selected_role == "trainee" or ("trainee" in raw_email or raw_email.startswith("tr-")):
        # Validate Trainee requirement: must be @ggmail.com
        if not raw_email.endswith("@ggmail.com"):
            raise HTTPException(
                status_code=400,
                detail="Trainee login must contain your Trainee ID ending in '@ggmail.com' (e.g., TR-8041@ggmail.com or trainee123@ggmail.com)."
            )
        
        trainee_id_part = raw_email.split("@")[0].upper()
        if not trainee_id_part:
            raise HTTPException(status_code=400, detail="Invalid Trainee ID in email.")

        user = UserProfile(
            email=raw_email,
            role="trainee",
            user_id=trainee_id_part,
            display_name=f"Trainee Clinician ({trainee_id_part})",
            permissions=[
                "view_blinded_workspace",
                "consult_patient_avatar",
                "order_multimodal_labs",
                "order_imaging_scans",
                "submit_differential_diagnosis",
                "view_progression_scenarios"
            ]
        )
        return LoginResponse(
            success=True,
            user=user,
            message=f"Welcome, Trainee Clinician ({trainee_id_part}). Entering Blinded Simulation Workstation."
        )

    elif selected_role == "supervisor" or ("supervisor" in raw_email or raw_email.startswith("sup-") or "prof" in raw_email or "eval" in raw_email):
        # Validate Supervisor login
        if not ("@" in raw_email and "." in raw_email):
            raise HTTPException(
                status_code=400,
                detail="Supervisor login requires a valid institutional email (e.g., SUP-001@ggmail.com or supervisor@ggmail.com)."
            )

        supervisor_id = raw_email.split("@")[0].upper()
        user = UserProfile(
            email=raw_email,
            role="supervisor",
            user_id=supervisor_id,
            display_name=f"Clinical Supervisor ({supervisor_id})",
            permissions=[
                "view_unblinded_workspace",
                "full_ground_truth_access",
                "generate_synthetic_avatars",
                "run_adversarial_arena",
                "view_trainee_oversight",
                "audit_consistency_privacy",
                "export_benchmark_metrics",
                "access_literature_evidence"
            ]
        )
        return LoginResponse(
            success=True,
            user=user,
            message=f"Supervisor mode authenticated ({supervisor_id}). Full ground-truth and evaluation arena unlocked."
        )

    else:
        # Default handling: check domain
        if raw_email.endswith("@ggmail.com"):
            trainee_id_part = raw_email.split("@")[0].upper()
            user = UserProfile(
                email=raw_email,
                role="trainee",
                user_id=trainee_id_part,
                display_name=f"Trainee Clinician ({trainee_id_part})",
                permissions=["view_blinded_workspace", "consult_patient_avatar", "order_multimodal_labs", "submit_differential_diagnosis"]
            )
            return LoginResponse(
                success=True,
                user=user,
                message=f"Authenticated as Trainee {trainee_id_part}."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Please specify your portal role (Trainee or Supervisor) and ensure Trainee email ends in '@ggmail.com'."
            )


@router.post("/trainee-submit-diagnosis", response_model=TraineeDiagnosisEvaluation)
def submit_trainee_diagnosis(payload: TraineeDiagnosisSubmission):
    """
    Evaluate a trainee's diagnosis submission against unblinded ground truth for an active patient avatar.
    Returns instant feedback, accuracy scoring, efficiency score, and missed hallmark analysis.
    """
    patient = state_manager.get_patient(payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient avatar {payload.patient_id} not found.")

    gt_disease_id = patient.disease.disease_id.lower()
    gt_disease_name = patient.disease.disease_name
    primary = payload.primary_diagnosis.strip().lower()

    # Check match against disease ID and name
    is_correct = (gt_disease_id in primary) or (any(part.lower() in primary for part in gt_disease_name.split() if len(part) > 4))

    diff_match = any(
        (gt_disease_id in d.lower()) or (any(part.lower() in d.lower() for part in gt_disease_name.split() if len(part) > 4))
        for d in payload.differential_diagnoses
    )

    if is_correct:
        accuracy = 95.0
    elif diff_match:
        accuracy = 65.0
    else:
        accuracy = 25.0

    # Calculate test efficiency: penalize ordering excessive non-informative tests
    tests_count = len(payload.ordered_investigations)
    efficiency = max(35.0, min(100.0, 100.0 - (max(0, tests_count - 4) * 8.0)))

    # Hallmarks detection according to disease
    detected: List[str] = []
    missed: List[str] = []

    ordered_lower = [t.lower() for t in payload.ordered_investigations]
    justification_lower = payload.clinical_justification.lower()

    if "wilson" in gt_disease_id:
        if any("ceruloplasmin" in t for t in ordered_lower) or "ceruloplasmin" in justification_lower:
            detected.append("Serum Ceruloplasmin (<20 mg/dL)")
        else:
            missed.append("Serum Ceruloplasmin Screening")

        if any("copper" in t for t in ordered_lower) or "copper" in justification_lower:
            detected.append("24h Urinary Copper Excretion (>100 ug/24h)")
        else:
            missed.append("24-Hour Urinary Copper Quantitation")

        if any("slit" in t or "kayser" in t for t in ordered_lower) or "kayser" in justification_lower:
            detected.append("Kayser-Fleischer Ring on Slit-Lamp Examination")
        else:
            missed.append("Slit-Lamp Examination for Kayser-Fleischer Rings")

    elif "fabry" in gt_disease_id:
        if any("galactosidase" in t for t in ordered_lower) or "galactosidase" in justification_lower:
            detected.append("Leukocyte Alpha-Galactosidase A Assay (<1.0 nmol/h/mg)")
        else:
            missed.append("Alpha-Galactosidase A Biochemical Assay")

        if any("lyso" in t or "gb3" in t for t in ordered_lower) or "lyso" in justification_lower:
            detected.append("Plasma Globotriaosylsphingosine (Lyso-Gb3)")
        else:
            missed.append("Plasma Lyso-Gb3 Biomarker")

    elif "gaucher" in gt_disease_id:
        if any("glucocerebrosidase" in t for t in ordered_lower) or "glucocerebrosidase" in justification_lower:
            detected.append("Beta-Glucocerebrosidase Deficiency (<15% reference)")
        else:
            missed.append("Beta-Glucocerebrosidase Leukocyte Assay")

        if any("spleen" in t or "ultrasound" in t or "mri" in t for t in ordered_lower) or "splenomegaly" in justification_lower:
            detected.append("Splenomegaly Documentation (Volumetric Scan)")
        else:
            missed.append("Spleen/Liver Volumetric Imaging")

    # Generate supervisory debriefing
    if is_correct:
        debrief = f"Confirmed diagnosis of {gt_disease_name}. Excellent clinical acumen with appropriate diagnostic pathway."
        if missed:
            debrief += f" Consider confirming with: {', '.join(missed)} for guideline compliance."
    elif diff_match:
        debrief = f"Correct diagnosis ({gt_disease_name}) was considered as a differential, but missed as primary. Review cardinal hallmark tests."
    else:
        debrief = f"Incorrect primary diagnosis. True diagnosis was {gt_disease_name}. Review pathognomonic laboratory markers: {', '.join(missed)}."

    evaluation = TraineeDiagnosisEvaluation(
        submission_id=f"sub-{uuid.uuid4().hex[:8]}",
        patient_id=payload.patient_id,
        trainee_id=payload.trainee_id,
        trainee_email=payload.trainee_email,
        primary_diagnosis=payload.primary_diagnosis,
        ground_truth_disease_id=gt_disease_id,
        ground_truth_disease_name=gt_disease_name,
        is_correct=is_correct,
        accuracy_score=accuracy,
        efficiency_score=efficiency,
        hallmarks_detected=detected,
        missed_hallmarks=missed,
        supervisor_debriefing=debrief,
        submitted_at_utc=datetime.now(timezone.utc).isoformat()
    )

    _trainee_submissions_store.insert(0, evaluation)
    return evaluation


@router.get("/supervisor/trainee-records", response_model=Dict[str, Any])
def get_supervisor_trainee_records():
    """Return all recorded trainee submissions and cohort performance metrics for the Supervisor Dashboard."""
    records = _trainee_submissions_store
    total = len(records)
    correct_count = sum(1 for r in records if r.is_correct)
    pass_rate = (correct_count / total * 100.0) if total > 0 else 0.0
    avg_accuracy = (sum(r.accuracy_score for r in records) / total) if total > 0 else 0.0
    avg_efficiency = (sum(r.efficiency_score for r in records) / total) if total > 0 else 0.0

    return {
        "summary": {
            "total_trainee_submissions": total,
            "correct_diagnoses_count": correct_count,
            "overall_pass_rate_pct": round(pass_rate, 1),
            "average_accuracy_score": round(avg_accuracy, 1),
            "average_test_efficiency": round(avg_efficiency, 1)
        },
        "submissions": records
    }
