"""Synthetic Rare-Disease Patient Specification Generator."""
import uuid
import datetime
import numpy as np
from typing import Optional
from app.disease_models import disease_registry
from app.knowledge.evidence_base import evidence_base
from app.schemas.patient import (
    SyntheticPatientSpecification, Demographics, EvidenceReference
)


class PatientGenerator:
    def generate_patient(
        self,
        disease_id: str = "wilson_disease",
        age_years: Optional[int] = None,
        biological_sex: Optional[str] = None,
        phenotype: Optional[str] = None,
        seed: Optional[int] = None
    ) -> SyntheticPatientSpecification:
        if seed is None:
            seed = int(np.random.randint(100000, 999999))

        rng = np.random.default_rng(seed)

        model = disease_registry.get_model(disease_id)
        if not model:
            raise ValueError(f"Unsupported disease_id: '{disease_id}'. Available: {[d['disease_id'] for d in disease_registry.list_available_diseases()]}")

        # Demographics
        if biological_sex is None:
            # Fabry is X-linked; male predominance for severe classical phenotype
            if disease_id == "fabry_disease":
                biological_sex = "Male" if rng.uniform() < 0.8 else "Female"
            else:
                biological_sex = "Male" if rng.uniform() < 0.5 else "Female"

        if age_years is None:
            if disease_id == "wilson_disease":
                age_years = int(rng.integers(14, 38))
            elif disease_id == "fabry_disease":
                age_years = int(rng.integers(18, 45))
            else:  # Gaucher
                age_years = int(rng.integers(12, 42))

        ethnicities = ["Caucasian", "Ashkenazi Jewish", "South Asian", "East Asian", "Hispanic", "African American"]
        if disease_id == "gaucher_disease" and rng.uniform() < 0.4:
            ethnicity = "Ashkenazi Jewish"
        else:
            ethnicity = str(rng.choice(ethnicities))

        if seed is not None:
            seed_hex = hex(abs(seed) % 0xFFFFFF)[2:].upper().zfill(6)
            patient_uuid = f"SYNTH-{disease_id[:3].upper()}-{seed_hex}"
        else:
            patient_uuid = f"SYNTH-{disease_id[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

        demographics = Demographics(
            synthetic_id=patient_uuid,
            age_years=age_years,
            biological_sex=biological_sex,
            ethnicity=ethnicity,
            synthetic_seed=seed,
            is_pediatric=(age_years < 18)
        )

        # Phenotype & Stage
        available_phenotypes = model.supported_phenotypes
        chosen_phenotype = phenotype if phenotype in available_phenotypes else str(rng.choice(available_phenotypes))
        disease_stage = "Active Moderate-to-Severe Presentation"

        current_month = 0

        # Generate Clinical Data
        symptoms = model.generate_symptoms(age_years, disease_stage, chosen_phenotype, rng)
        labs = model.generate_laboratory_trajectories(current_month, disease_stage, chosen_phenotype, rng)
        imaging = model.generate_imaging_studies(current_month, disease_stage, chosen_phenotype, rng)
        notes = model.generate_encounter_notes(current_month, disease_stage, symptoms, rng)
        scenarios = model.generate_treatment_scenarios(current_month, disease_stage, chosen_phenotype)

        # Build evidence catalog
        evidence_catalog = {}
        for k in model.evidence_keys:
            ref = evidence_base.get_evidence(k)
            if ref:
                evidence_catalog[k] = ref

        return SyntheticPatientSpecification(
            patient_id=patient_uuid,
            demographics=demographics,
            disease=model.metadata,
            baseline_disease_stage=disease_stage,
            current_simulation_month=current_month,
            symptoms=symptoms,
            lab_history=labs,
            imaging_studies=imaging,
            clinical_notes=notes,
            treatment_scenarios=scenarios,
            active_treatment=None,
            evidence_catalog=evidence_catalog,
            created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            reproducibility_seed=seed
        )


patient_generator = PatientGenerator()
