"""Main FastAPI Application Entrypoint."""
import os
import sys

# Ensure backend root is in sys.path so app.* modules resolve correctly
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_patients import router as patients_router
from app.api.routes_simulation import router as simulation_router
from app.api.routes_validation import router as validation_router
from app.api.routes_diagnostic import router as diagnostic_router
from app.api.routes_evidence import router as evidence_router
from app.api.routes_arena import router as arena_router
from app.api.routes_auth import router as auth_router
from app.api.routes_what_if import router as what_if_router
from app.api.routes_mystery import router as mystery_router
from app.api.routes_populations import router as populations_router

from app.generators.patient_generator import patient_generator
from app.engine.state_manager import state_manager

app = FastAPI(
    title="Rare-Disease Synthetic Patient Avatars (PS3)",
    description=(
        "High-fidelity, multimodal generative AI system for synthetic rare-disease patient avatars. "
        "Grounded in published medical literature (PubMed) and expert-validated pathophysiological models. "
        "Supports interactive clinician training, explicit uncertainty bounds, privacy auditing, "
        "and controlled diagnostic algorithm stress-testing."
    ),
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Include API Routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(simulation_router)
app.include_router(validation_router)
app.include_router(diagnostic_router)
app.include_router(evidence_router)
app.include_router(arena_router)
app.include_router(what_if_router)
app.include_router(mystery_router)
app.include_router(populations_router)



@app.on_event("startup")
def bootstrap_initial_avatars():
    """Seed system with high-fidelity avatars for each supported rare disease."""
    diseases = [
        ("wilson_disease", 22, "Male", "Mixed Hepato-Neurological", 42001),
        ("fabry_disease", 31, "Male", "Classic Early-Onset", 53002),
        ("gaucher_disease", 26, "Female", "Classic Non-Neuronopathic Type 1", 64003)
    ]
    for d_id, age, sex, phenotype, seed in diseases:
        try:
            pt = patient_generator.generate_patient(
                disease_id=d_id,
                age_years=age,
                biological_sex=sex,
                phenotype=phenotype,
                seed=seed
            )
            state_manager.register_patient(pt)
            print(f"[BOOTSTRAP] Initialized avatar {pt.patient_id} for {pt.disease.disease_name}")
        except Exception as e:
            print(f"[BOOTSTRAP ERROR] Failed to initialize {d_id}: {e}")


# Serve Frontend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
