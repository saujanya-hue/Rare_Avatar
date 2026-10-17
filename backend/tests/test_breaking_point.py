"""Unit and Integration Tests for Diagnostic AI Breaking Point Finder."""
import pytest
from fastapi.testclient import TestClient

from app.main import app, bootstrap_initial_avatars
from app.schemas.diagnostic import (
    BreakingPointSearchConfig, BreakingPointComparisonConfig,
    BreakingPointResult, BreakingPointComparisonReport
)
from app.stress_testing.adversarial_arena import adversarial_arena_engine


@pytest.fixture(scope="module", autouse=True)
def init_app():
    bootstrap_initial_avatars()


@pytest.fixture
def client():
    return TestClient(app)


def test_breaking_point_search_fragile_noise():
    """Verify breaking point finder identifies minimal valid delta on fragile model."""
    config = BreakingPointSearchConfig(
        disease_id="wilson_disease",
        random_seed=42,
        model_type="mock_fragile",
        search_axis="noise_sigma",
        max_steps=10,
        step_size=0.03,
        target_failure_type="ANY"
    )
    result = adversarial_arena_engine.find_breaking_point(config)

    assert isinstance(result, BreakingPointResult)
    assert result.disease_id == "wilson_disease"
    assert result.model_name is not None
    assert result.search_axis == "noise_sigma"
    assert len(result.step_history) > 0
    assert result.steps_evaluated == len(result.step_history)
    assert result.clinical_interpretation != ""

    # Each step should record clinical validity
    for step in result.step_history:
        assert isinstance(step.is_clinically_valid, bool)
        assert step.step_index >= 1


def test_breaking_point_search_confounding_infection():
    """Verify that mock_fragile model breaks under acute infection confounders."""
    config = BreakingPointSearchConfig(
        disease_id="wilson_disease",
        random_seed=101,
        model_type="mock_fragile",
        search_axis="confounding_infection",
        max_steps=5,
        target_failure_type="MISDIAGNOSIS"
    )
    result = adversarial_arena_engine.find_breaking_point(config)

    assert result.breaking_point_found is True
    assert result.failure_type == "MISDIAGNOSIS"
    assert result.minimal_delta is not None
    assert result.minimal_delta["inject_confounding_infection"] is True
    assert result.breaking_prediction is not None
    assert result.breaking_prediction.is_top1_correct is False
    assert len(result.affected_features) > 0


def test_breaking_point_comparison_resilience_ranking():
    """Verify multi-model breaking point comparison ranks resilience properly."""
    config = BreakingPointComparisonConfig(
        disease_id="wilson_disease",
        random_seed=42,
        models=["mock_fragile", "mock_robust"],
        search_axis="noise_sigma",
        max_steps=8,
        step_size=0.04
    )
    report = adversarial_arena_engine.compare_models_breaking_point(config)

    assert isinstance(report, BreakingPointComparisonReport)
    assert "mock_fragile" in report.results
    assert "mock_robust" in report.results
    assert len(report.resilience_ranking) == 2

    # Robust model should have equal or higher resilience score than fragile model
    fragile_rank = next(r for r in report.resilience_ranking if r["model_type"] == "mock_fragile")
    robust_rank = next(r for r in report.resilience_ranking if r["model_type"] == "mock_robust")
    assert robust_rank["resilience_score"] >= fragile_rank["resilience_score"]


def test_breaking_point_api_endpoints(client):
    """Test REST API endpoints for search and compare."""
    # Test Search Endpoint
    search_payload = {
        "disease_id": "fabry_disease",
        "random_seed": 55,
        "model_type": "mock_fragile",
        "search_axis": "noise_sigma",
        "max_steps": 6,
        "step_size": 0.03,
        "target_failure_type": "ANY"
    }
    resp = client.post("/api/diagnostic-arena/breaking-point/search", json=search_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["disease_id"] == "fabry_disease"
    assert "step_history" in data
    assert "clinical_interpretation" in data

    # Test Compare Endpoint
    compare_payload = {
        "disease_id": "gaucher_disease",
        "random_seed": 77,
        "models": ["mock_fragile", "reference_baseline"],
        "search_axis": "noise_sigma",
        "max_steps": 5,
        "step_size": 0.03
    }
    resp_cmp = client.post("/api/diagnostic-arena/breaking-point/compare", json=compare_payload)
    assert resp_cmp.status_code == 200
    cmp_data = resp_cmp.json()
    assert cmp_data["disease_id"] == "gaucher_disease"
    assert "resilience_ranking" in cmp_data
    assert len(cmp_data["resilience_ranking"]) == 2
