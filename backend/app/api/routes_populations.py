"""REST API routes for Synthetic Patient Population Lab."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response

from app.schemas.population import (
    PopulationCohortConfig, PopulationCohortRecord
)
from app.generators.population_generator import population_generator

router = APIRouter(prefix="/api/populations", tags=["Synthetic Patient Population Lab"])


@router.post("/generate", response_model=PopulationCohortRecord)
def generate_population_cohort(config: PopulationCohortConfig):
    """
    Generate a batch cohort of synthetic rare-disease patient avatars.
    Executes automated 5-category Consistency Guardian validation on all members,
    and computes cohort-level demographic, staging, and biomarker distributions.
    """
    try:
        return population_generator.generate_cohort(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cohort generation failed: {str(e)}")


@router.get("/cohorts", response_model=List[PopulationCohortRecord])
def list_population_cohorts():
    """List all synthetic patient population cohorts generated in the current session."""
    return population_generator.list_cohorts()


@router.get("/cohorts/{cohort_id}", response_model=PopulationCohortRecord)
def get_population_cohort(cohort_id: str):
    """Retrieve full demographic summaries, validation metrics, and member roster for a cohort."""
    cohort = population_generator.get_cohort(cohort_id)
    if not cohort:
        raise HTTPException(status_code=404, detail=f"Cohort '{cohort_id}' not found.")
    return cohort


@router.get("/cohorts/{cohort_id}/export")
def export_population_cohort(cohort_id: str, format: str = Query("json", pattern="^(json|csv)$")):
    """Export population cohort roster and distribution analytics as CSV or JSON."""
    cohort = population_generator.get_cohort(cohort_id)
    if not cohort:
        raise HTTPException(status_code=404, detail=f"Cohort '{cohort_id}' not found.")

    if format == "csv":
        csv_data = population_generator.export_cohort_csv(cohort_id)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=population_{cohort_id}.csv"}
        )
    else:
        json_data = population_generator.export_cohort_json(cohort_id)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=population_{cohort_id}.json"}
        )
