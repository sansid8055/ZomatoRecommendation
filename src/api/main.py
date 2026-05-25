"""FastAPI backend for Zomato AI Restaurant Recommendations."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.data.models import UserPreferences
from src.data.repository import RestaurantRepository
from src.services.orchestrator import RecommendationOrchestrator
from src.services.schemas import RecommendationResponse

logger = logging.getLogger(__name__)

_repository: RestaurantRepository | None = None
_orchestrator: RecommendationOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _repository, _orchestrator
    settings = get_settings()
    if not settings.data_cache_path.exists():
        logger.warning("Dataset not found at %s", settings.data_cache_path)
    else:
        _repository = RestaurantRepository()
        _repository.load()
        _orchestrator = RecommendationOrchestrator(repository=_repository)
        logger.info("API ready: %s locations loaded", len(_repository.get_available_locations()))
    yield
    _repository = None
    _orchestrator = None


app = FastAPI(
    title="Zomato AI Restaurant Recommendations API",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PreferencesRequest(BaseModel):
    location: str
    budget: str = Field(pattern="^(low|medium|high)$")
    cuisine: str | None = None
    min_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    additional_preferences: str | None = None


def _get_orchestrator() -> RecommendationOrchestrator:
    if _orchestrator is None:
        settings = get_settings()
        if not settings.data_cache_path.exists():
            raise HTTPException(
                status_code=503,
                detail={
                    "message": "Dataset not found. Run: python scripts/download_dataset.py",
                    "code": "DATASET_MISSING",
                },
            )
        raise HTTPException(
            status_code=503,
            detail={"message": "Service starting or dataset failed to load.", "code": "NOT_READY"},
        )
    return _orchestrator


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def config_status() -> dict[str, Any]:
    settings = get_settings()
    api_ok = bool(settings.groq_api_key and str(settings.groq_api_key).strip())
    dataset_ok = settings.data_cache_path.exists()
    return {
        "api_key_configured": api_ok,
        "dataset_ready": dataset_ok,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "top_k_results": settings.top_k_results,
        "max_candidates": settings.max_candidates,
    }


@app.get("/api/locations")
def list_locations() -> dict[str, list[str]]:
    if _repository is None or not _repository.is_loaded:
        raise HTTPException(status_code=503, detail="Repository not loaded")
    return {"locations": _repository.get_available_locations()}


@app.post("/api/recommendations", response_model=RecommendationResponse)
def create_recommendations(body: PreferencesRequest) -> RecommendationResponse:
    settings = get_settings()
    if not settings.groq_api_key or not str(settings.groq_api_key).strip():
        raise HTTPException(
            status_code=400,
            detail={
                "message": "GROQ_API_KEY is not set. Copy .env.example to .env and add your key.",
                "code": "API_KEY_MISSING",
            },
        )

    try:
        prefs = UserPreferences(
            location=body.location,
            budget=body.budget,  # type: ignore[arg-type]
            cuisine=body.cuisine,
            min_rating=body.min_rating if body.min_rating and body.min_rating > 0 else None,
            additional_preferences=body.additional_preferences,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    orchestrator = _get_orchestrator()
    response = orchestrator.get_recommendations(prefs, fail_without_api_key=True)

    if not response.success and response.message:
        raise HTTPException(
            status_code=400,
            detail={"message": response.message, "code": "REQUEST_FAILED"},
        )

    return response
