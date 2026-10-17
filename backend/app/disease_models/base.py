"""Abstract Base Class for Rare-Disease Pathophysiological Models."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from app.schemas.patient import (
    DiseaseMetadata, ClinicalSymptom, LabMeasurement, ImagingStudy,
    ClinicalEncounterNote, TreatmentResponseScenario, UncertaintyBounds
)


class BaseDiseaseModel(ABC):
    @property
    @abstractmethod
    def disease_id(self) -> str:
        pass

    @property
    @abstractmethod
    def metadata(self) -> DiseaseMetadata:
        pass

    @property
    @abstractmethod
    def supported_phenotypes(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def evidence_keys(self) -> List[str]:
        pass

    @abstractmethod
    def generate_symptoms(
        self, age_years: int, disease_stage: str, phenotype: str, rng
    ) -> List[ClinicalSymptom]:
        pass

    @abstractmethod
    def generate_laboratory_trajectories(
        self, current_month: int, disease_stage: str, phenotype: str, rng
    ) -> List[LabMeasurement]:
        pass

    @abstractmethod
    def generate_imaging_studies(
        self, current_month: int, disease_stage: str, phenotype: str, rng
    ) -> List[ImagingStudy]:
        pass

    @abstractmethod
    def generate_encounter_notes(
        self, current_month: int, disease_stage: str, symptoms: List[ClinicalSymptom], rng
    ) -> List[ClinicalEncounterNote]:
        pass

    @abstractmethod
    def generate_treatment_scenarios(
        self, current_month: int, disease_stage: str, phenotype: str
    ) -> List[TreatmentResponseScenario]:
        pass

    @abstractmethod
    def get_physiological_constraints(self) -> List[Dict[str, Any]]:
        """Returns rules for automated validation (ranges, cross-modal checks)."""
        pass
