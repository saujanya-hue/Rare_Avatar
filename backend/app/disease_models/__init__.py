from typing import Dict, List, Optional
from app.disease_models.base import BaseDiseaseModel
from app.disease_models.wilson_disease import WilsonDiseaseModel
from app.disease_models.fabry_disease import FabryDiseaseModel
from app.disease_models.gaucher_disease import GaucherDiseaseModel


class DiseaseModelRegistry:
    def __init__(self):
        self._models: Dict[str, BaseDiseaseModel] = {
            "wilson_disease": WilsonDiseaseModel(),
            "fabry_disease": FabryDiseaseModel(),
            "gaucher_disease": GaucherDiseaseModel()
        }

    def get_model(self, disease_id: str) -> Optional[BaseDiseaseModel]:
        return self._models.get(disease_id)

    def __contains__(self, disease_id: str) -> bool:
        return disease_id in self._models

    def __getitem__(self, disease_id: str) -> BaseDiseaseModel:
        if disease_id not in self._models:
            raise KeyError(f"Disease '{disease_id}' not found in registry.")
        return self._models[disease_id]

    def list_available_diseases(self) -> List[Dict[str, str]]:
        return [
            {
                "disease_id": m.disease_id,
                "disease_name": m.metadata.disease_name,
                "omim_id": m.metadata.omim_id,
                "orpha_code": m.metadata.orpha_code,
                "genetic_basis": m.metadata.genetic_basis
            }
            for m in self._models.values()
        ]


disease_registry = DiseaseModelRegistry()
