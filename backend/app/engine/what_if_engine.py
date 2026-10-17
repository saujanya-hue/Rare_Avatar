"""Clinical What-If Lab Engine.

Branching simulation engine with immutable snapshot isolation (`copy.deepcopy`),
counterfactual treatment scenario advancement, and multi-branch comparative analytics.
"""
import copy
import uuid
import datetime
import io
import csv
from typing import Dict, List, Tuple, Optional, Any

from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.simulation import (
    WhatIfBranchConfig, WhatIfTrajectoryPoint, WhatIfBranchState,
    WhatIfComparisonReport
)
from app.engine.state_manager import state_manager
from app.disease_models import disease_registry


class WhatIfEngine:
    def __init__(self):
        # Maps branch_id -> (WhatIfBranchState, SyntheticPatientSpecification snapshot)
        self._branches: Dict[str, Tuple[WhatIfBranchState, SyntheticPatientSpecification]] = {}

    def create_branch(self, config: WhatIfBranchConfig) -> WhatIfBranchState:
        patient = state_manager.get_patient(config.patient_id)
        if not patient:
            raise ValueError(f"Patient avatar '{config.patient_id}' not found.")

        # 1. Immutable snapshot isolation via deepcopy
        snapshot: SyntheticPatientSpecification = copy.deepcopy(patient)

        branch_id = f"BRANCH-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        d_id = snapshot.disease.disease_id
        d_name = snapshot.disease.disease_name

        # 2. Determine primary biomarker & baseline status
        marker_name, base_val, unit = self._get_primary_biomarker(snapshot)
        mean_symp = float(sum(s.severity_score for s in snapshot.symptoms) / max(1, len(snapshot.symptoms)))
        active_symps = len(snapshot.symptoms)

        init_point = WhatIfTrajectoryPoint(
            month=config.origin_month,
            primary_biomarker_name=marker_name,
            primary_biomarker_value=base_val,
            unit=unit,
            clinical_status="Baseline / Branch Origin",
            symptom_severity_mean=round(mean_symp, 1),
            active_symptoms_count=active_symps,
            ci_low=round(base_val * 0.90, 1),
            ci_high=round(base_val * 1.10, 1)
        )

        state = WhatIfBranchState(
            branch_id=branch_id,
            patient_id=config.patient_id,
            branch_name=config.branch_name,
            disease_id=d_id,
            disease_name=d_name,
            intervention_type=config.intervention_type,
            intervention_agent=config.intervention_agent,
            origin_month=config.origin_month,
            current_month=config.origin_month,
            is_active=True,
            trajectory=[init_point],
            created_at=created_at
        )

        self._branches[branch_id] = (state, snapshot)
        return state

    def advance_branch(self, branch_id: str, advance_months: int = 6) -> WhatIfBranchState:
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found in What-If registry.")

        state, snapshot = self._branches[branch_id]
        step_months = max(1, min(36, advance_months))
        target_month = state.current_month + step_months

        # Generate intermediate trajectory points at 3-month or 6-month intervals
        curr_m = state.current_month
        last_point = state.trajectory[-1]

        marker_name = last_point.primary_biomarker_name
        curr_val = last_point.primary_biomarker_value
        unit = last_point.unit
        curr_symp = last_point.symptom_severity_mean
        curr_symp_count = last_point.active_symptoms_count

        while curr_m < target_month:
            curr_m = min(target_month, curr_m + 6)

            # Trajectory dynamics governed by disease model and intervention type
            curr_val, curr_symp, curr_symp_count, status_desc = self._calculate_step_delta(
                disease_id=state.disease_id,
                intervention_type=state.intervention_type,
                intervention_agent=state.intervention_agent,
                current_val=curr_val,
                current_symp=curr_symp,
                symptom_count=curr_symp_count,
                elapsed_months=(curr_m - state.origin_month)
            )

            pt = WhatIfTrajectoryPoint(
                month=curr_m,
                primary_biomarker_name=marker_name,
                primary_biomarker_value=round(curr_val, 1),
                unit=unit,
                clinical_status=status_desc,
                symptom_severity_mean=round(max(0.0, min(10.0, curr_symp)), 1),
                active_symptoms_count=max(0, curr_symp_count),
                ci_low=round(curr_val * 0.88, 1),
                ci_high=round(curr_val * 1.12, 1)
            )
            state.trajectory.append(pt)

        state.current_month = target_month
        return state

    def compare_branches(self, patient_id: str, branch_ids: List[str]) -> WhatIfComparisonReport:
        comparison_id = f"WICMP-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        selected_states: Dict[str, WhatIfBranchState] = {}
        for b_id in branch_ids:
            if b_id in self._branches:
                st, _ = self._branches[b_id]
                if st.patient_id == patient_id:
                    selected_states[b_id] = st

        if not selected_states:
            raise ValueError(f"No valid branches found for comparison under patient '{patient_id}'.")

        # Collect timeline months across branches
        all_months = set()
        for b in selected_states.values():
            for p in b.trajectory:
                all_months.add(p.month)
        sorted_months = sorted(list(all_months))

        # Comparative metrics table
        metrics = []
        first_branch = next(iter(selected_states.values()))
        d_id = first_branch.disease_id
        d_name = first_branch.disease_name

        for b_id, st in selected_states.items():
            start_p = st.trajectory[0]
            end_p = st.trajectory[-1]
            delta_val = end_p.primary_biomarker_value - start_p.primary_biomarker_value
            delta_symp = end_p.symptom_severity_mean - start_p.symptom_severity_mean

            metrics.append({
                "branch_id": b_id,
                "branch_name": st.branch_name,
                "intervention_type": st.intervention_type,
                "intervention_agent": st.intervention_agent,
                "duration_months": end_p.month - start_p.month,
                "biomarker_start": start_p.primary_biomarker_value,
                "biomarker_end": end_p.primary_biomarker_value,
                "biomarker_delta": round(delta_val, 1),
                "biomarker_unit": start_p.unit,
                "symptom_severity_delta": round(delta_symp, 1),
                "terminal_clinical_status": end_p.clinical_status
            })

        # Evidence-grounded clinical recommendation
        recommendation = self._generate_comparative_recommendation(d_id, metrics)

        return WhatIfComparisonReport(
            comparison_id=comparison_id,
            patient_id=patient_id,
            disease_id=d_id,
            disease_name=d_name,
            branches=selected_states,
            timeline_months=sorted_months,
            comparative_metrics=metrics,
            clinical_recommendation=recommendation,
            created_at=created_at
        )

    def list_patient_branches(self, patient_id: str) -> List[WhatIfBranchState]:
        return [state for state, _ in self._branches.values() if state.patient_id == patient_id]

    def get_branch_state(self, branch_id: str) -> Optional[WhatIfBranchState]:
        if branch_id in self._branches:
            return self._branches[branch_id][0]
        return None

    def export_branch_csv(self, branch_id: str) -> str:
        if branch_id not in self._branches:
            raise ValueError(f"Branch '{branch_id}' not found.")

        state, _ = self._branches[branch_id]
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "branch_id", "branch_name", "disease_name", "intervention_type",
            "intervention_agent", "month", "primary_biomarker", "value",
            "unit", "ci_low", "ci_high", "symptom_severity_mean", "active_symptoms_count", "clinical_status"
        ])

        for pt in state.trajectory:
            writer.writerow([
                state.branch_id,
                state.branch_name,
                state.disease_name,
                state.intervention_type,
                state.intervention_agent,
                pt.month,
                pt.primary_biomarker_name,
                pt.primary_biomarker_value,
                pt.unit,
                pt.ci_low,
                pt.ci_high,
                pt.symptom_severity_mean,
                pt.active_symptoms_count,
                pt.clinical_status
            ])

        return output.getvalue()

    def _get_primary_biomarker(self, patient: SyntheticPatientSpecification) -> Tuple[str, float, str]:
        lab_dict = {l.test_code: l for l in patient.lab_history}
        d_id = patient.disease.disease_id

        if d_id == "wilson_disease":
            lab = lab_dict.get("URINARY_COPPER_24H")
            if lab:
                return ("24h Urinary Copper", float(lab.value), lab.unit)
            return ("Serum Ceruloplasmin", 8.5, "mg/dL")

        elif d_id == "fabry_disease":
            lab = lab_dict.get("LYSO_GB3")
            if lab:
                return ("Plasma Lyso-Gb3", float(lab.value), lab.unit)
            return ("Plasma Lyso-Gb3", 28.0, "ng/mL")

        else:  # Gaucher
            lab = lab_dict.get("PLATELETS")
            if lab:
                return ("Platelet Count", float(lab.value), lab.unit)
            return ("Plasma Lyso-Gb1", 145.0, "ng/mL")

    def _calculate_step_delta(
        self, disease_id: str, intervention_type: str, intervention_agent: str,
        current_val: float, current_symp: float, symptom_count: int, elapsed_months: int
    ) -> Tuple[float, float, int, str]:
        # Branch Dynamics Matrix
        agent_lower = intervention_agent.lower()
        is_treated = ("targeted" in intervention_type.lower() or "chelation" in agent_lower or "ert" in agent_lower or "penicillamine" in agent_lower or "agalsidase" in agent_lower or "imiglucerase" in agent_lower)

        if disease_id == "wilson_disease":
            if is_treated:
                # Urinary copper decreases toward stable controlled range (35-70 ug/24h)
                new_val = max(45.0, current_val * 0.78)
                new_symp = max(1.0, current_symp - 0.7)
                new_count = max(1, symptom_count - 1 if elapsed_months >= 12 else symptom_count)
                status = f"Stable response to {intervention_agent}; negative copper balance achieved."
            elif "delay" in intervention_type.lower():
                new_val = current_val * 1.05
                new_symp = current_symp + 0.3
                new_count = symptom_count
                status = "Delayed intervention; persistent hepatic/neurological copper accumulation."
            else:  # Untreated natural history
                new_val = min(420.0, current_val * 1.15)
                new_symp = min(10.0, current_symp + 0.8)
                new_count = symptom_count + 1
                status = "Untreated progression; progressive copper toxicity and cirrhosis risk."

        elif disease_id == "fabry_disease":
            if is_treated:
                # Lyso-Gb3 drops exponentially by ~40-60% under ERT
                new_val = max(1.8, current_val * 0.62)
                new_symp = max(1.5, current_symp - 0.8)
                new_count = max(1, symptom_count - 1 if elapsed_months >= 12 else symptom_count)
                status = f"Therapeutic Gb3 substrate clearance under {intervention_agent}; pain stabilization."
            elif "delay" in intervention_type.lower():
                new_val = current_val * 1.08
                new_symp = current_symp + 0.4
                new_count = symptom_count
                status = "Delayed ERT start; progressive microvascular endothelial deposition."
            else:  # Untreated
                new_val = min(120.0, current_val * 1.18)
                new_symp = min(10.0, current_symp + 0.9)
                new_count = symptom_count + 1
                status = "Unchecked glycosphingolipid accumulation; progressive renal/cardiac deterioration."

        else:  # Gaucher
            if is_treated:
                # Platelet count recovers progressively (+20k/uL per step up to 180k)
                new_val = min(190.0, current_val + 24.0)
                new_symp = max(0.5, current_symp - 1.0)
                new_count = max(0, symptom_count - 1 if elapsed_months >= 12 else symptom_count)
                status = f"Hematological recovery under {intervention_agent}; spleen reduction & marrow clearance."
            elif "delay" in intervention_type.lower():
                new_val = max(35.0, current_val - 3.0)
                new_symp = current_symp + 0.3
                new_count = symptom_count
                status = "Delayed ERT; unresolved hypersplenism and persistent bleeding risk."
            else:  # Untreated
                new_val = max(28.0, current_val - 12.0)
                new_symp = min(10.0, current_symp + 1.1)
                new_count = symptom_count + 1
                status = "Severe untreated hypersplenism, cytopenias, and progressive skeletal osteopenia."

        return (new_val, new_symp, new_count, status)

    def _generate_comparative_recommendation(self, disease_id: str, metrics: List[Dict[str, Any]]) -> str:
        treated_branches = [m for m in metrics if "targeted" in m["intervention_type"].lower()]
        untreated_branches = [m for m in metrics if "untreated" in m["intervention_type"].lower() or "delay" in m["intervention_type"].lower()]

        if treated_branches and untreated_branches:
            t = treated_branches[0]
            u = untreated_branches[0]
            return (
                f"Comparative simulation demonstrates marked divergence over {t['duration_months']} months. "
                f"Branch '{t['branch_name']}' achieved primary biomarker control ({t['biomarker_end']} {t['biomarker_unit']}) "
                f"with symptom severity reduction of {abs(t['symptom_severity_delta']):.1f} points. In contrast, "
                f"Branch '{u['branch_name']}' showed disease progression to '{u['terminal_clinical_status']}'. "
                f"Early initiation of disease-modifying therapy is strongly substantiated by clinical practice guidelines."
            )
        else:
            return "Comparative branches demonstrate distinct pathophysiological trajectories under simulated interventions."


what_if_engine = WhatIfEngine()
