"""REST API routes for Diagnostic AI Adversarial Arena."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse

from app.schemas.diagnostic import (
    ArenaExperimentConfig, ArenaExperimentResult,
    ArenaCaseRecord, ArenaCapabilityInfo,
    BreakingPointSearchConfig, BreakingPointResult,
    BreakingPointComparisonConfig, BreakingPointComparisonReport
)
from app.stress_testing.adversarial_arena import adversarial_arena_engine

router = APIRouter(prefix="/api/diagnostic-arena", tags=["Diagnostic AI Adversarial Arena"])


@router.get("/capabilities", response_model=ArenaCapabilityInfo)
def get_arena_capabilities():
    """Retrieve supported disease models, perturbation categories, diagnostic models, and clinical constraints."""
    return adversarial_arena_engine.get_capabilities()


@router.post("/experiments/run", response_model=ArenaExperimentResult)
def run_adversarial_experiment(config: ArenaExperimentConfig):
    """
    Execute an automated adversarial diagnostic stress-testing experiment.
    Generates synthetic patient scenarios, applies controlled constraint-aware perturbations,
    evaluates baseline and perturbed diagnostic models, and computes benchmark metrics.
    """
    try:
        result = adversarial_arena_engine.run_experiment(config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adversarial experiment failed: {str(e)}")


@router.get("/experiments", response_model=List[Dict[str, Any]])
def list_experiment_history():
    """List historical experiment runs with summary metrics."""
    return adversarial_arena_engine.list_experiments()


@router.get("/experiments/{experiment_id}", response_model=ArenaExperimentResult)
def get_experiment_details(experiment_id: str):
    """Retrieve full experiment details, benchmark metrics, and all case records."""
    exp = adversarial_arena_engine.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return exp


@router.get("/cases/{case_id}", response_model=ArenaCaseRecord)
def inspect_case_record(case_id: str):
    """Inspect an individual adversarial case record with diff, applied transformations, and validation details."""
    case = adversarial_arena_engine.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found in arena registry.")
    return case


@router.get("/experiments/{experiment_id}/export")
def export_experiment(experiment_id: str, format: str = Query("json", pattern="^(json|csv)$")):
    """Export benchmark summary, configuration, and case-level results as JSON or CSV."""
    exp = adversarial_arena_engine.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")

    if format == "csv":
        csv_data = adversarial_arena_engine.export_experiment_csv(experiment_id)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=arena_benchmark_{experiment_id}.csv"}
        )
    else:
        json_data = adversarial_arena_engine.export_experiment_json(experiment_id)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=arena_benchmark_{experiment_id}.json"}
        )


@router.post("/breaking-point/search", response_model=BreakingPointResult)
def search_breaking_point(config: BreakingPointSearchConfig):
    """
    Search for the minimal clinically valid modification that breaks diagnostic prediction.
    Iteratively increases perturbation along selected axis while enforcing disease invariants,
    evaluating the model until failure (misdiagnosis or confidence collapse) is triggered.
    """
    try:
        result = adversarial_arena_engine.find_breaking_point(config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breaking point search failed: {str(e)}")


@router.post("/breaking-point/compare", response_model=BreakingPointComparisonReport)
def compare_breaking_point(config: BreakingPointComparisonConfig):
    """
    Compare breaking points and algorithmic resilience across multiple diagnostic models
    on the exact same synthetic rare-disease patient avatar.
    """
    try:
        report = adversarial_arena_engine.compare_models_breaking_point(config)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breaking point comparison failed: {str(e)}")
