"""API response DTOs for the recommendation orchestrator (Phase 4)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResponseMetadata(BaseModel):
    """Diagnostics and filter context for clients and logging."""

    candidate_count: int = Field(
        description="Number of candidates sent to the LLM (after cap)."
    )
    total_matched: int = Field(
        description="Restaurants matching filters before LLM cap."
    )
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    filter_duration_ms: float | None = None
    llm_duration_ms: float | None = None
    prompt_token_estimate: int | None = None
    degraded_mode: bool = False


class RankedRecommendation(BaseModel):
    """UI-ready recommendation card (repository fields + LLM explanation)."""

    rank: int = Field(ge=1)
    restaurant_id: str
    name: str
    cuisine: str
    rating: float | None = None
    approx_cost: int | None = None
    location: str
    locality: str | None = None
    explanation: str


class RecommendationResponse(BaseModel):
    """Full orchestrator output."""

    success: bool = True
    summary: str | None = None
    recommendations: list[RankedRecommendation] = Field(default_factory=list)
    metadata: ResponseMetadata
    message: str | None = None
    suggestions: list[str] = Field(default_factory=list)
