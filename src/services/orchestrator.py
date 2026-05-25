"""End-to-end recommendation orchestration (Phase 4)."""

from __future__ import annotations

import logging
import time
from typing import Any

from src.config.settings import get_settings
from src.data.models import Restaurant, UserPreferences
from src.data.repository import RestaurantRepository
from src.domain.filters import cuisine_match_score, restaurant_dedupe_key, validate_preferences
from src.llm.client import RecommendationLLM
from src.llm.engine import RecommendationEngine
from src.llm.models import LLMRecommendationOutput
from src.llm.prompts import build_prompts
from src.services.schemas import (
    RankedRecommendation,
    RecommendationResponse,
    ResponseMetadata,
)

logger = logging.getLogger(__name__)

FILTER_ERROR_MESSAGE = "Something went wrong while searching. Please try again."
LLM_ERROR_MESSAGE = (
    "Recommendation service encountered an error. Showing top-rated matches instead."
)
MISSING_API_KEY_MESSAGE = (
    "API key not configured. Copy .env.example to .env and set GROQ_API_KEY."
)


def estimate_prompt_tokens(system_prompt: str, user_prompt: str) -> int:
    """Rough token estimate (~4 characters per token)."""
    return (len(system_prompt) + len(user_prompt)) // 4


def _format_cuisine(restaurant: Restaurant) -> str:
    return ", ".join(restaurant.cuisines) if restaurant.cuisines else "Not specified"


def _template_backfill_explanation(restaurant: Restaurant, prefs: UserPreferences) -> str:
    rating_text = (
        f"{restaurant.rating} stars" if restaurant.rating is not None else "well-reviewed"
    )
    cost_text = (
        f"₹{restaurant.approx_cost} for two"
        if restaurant.approx_cost
        else "reasonable pricing"
    )
    return (
        f"{restaurant.name} is a strong match in {prefs.location} with {rating_text}, "
        f"fitting your {prefs.budget} budget ({cost_text})."
    )


def _enrich_recommendations(
    llm_output: LLMRecommendationOutput,
    repository: RestaurantRepository,
    *,
    candidates: list[Restaurant] | None = None,
    prefs: UserPreferences | None = None,
    top_k: int = 5,
) -> list[RankedRecommendation]:
    """Join LLM ranks with repository rows; dedupe chains; backfill to top_k (ORC-03/04)."""
    if not llm_output.recommendations and not candidates:
        return []

    ordered_ids = [item.restaurant_id for item in llm_output.recommendations]
    by_id = {r.id: r for r in repository.get_by_ids(ordered_ids)}

    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    enriched: list[RankedRecommendation] = []

    def _try_append(
        restaurant: Restaurant,
        explanation: str,
    ) -> bool:
        if restaurant.id in seen_ids:
            return False
        key = restaurant_dedupe_key(restaurant)
        if key in seen_keys:
            return False
        seen_ids.add(restaurant.id)
        seen_keys.add(key)
        enriched.append(
            RankedRecommendation(
                rank=len(enriched) + 1,
                restaurant_id=restaurant.id,
                name=restaurant.name,
                cuisine=_format_cuisine(restaurant),
                rating=restaurant.rating,
                approx_cost=restaurant.approx_cost,
                location=restaurant.location,
                locality=restaurant.locality,
                explanation=explanation,
            )
        )
        return True

    for item in sorted(llm_output.recommendations, key=lambda x: x.rank):
        restaurant = by_id.get(item.restaurant_id)
        if restaurant is None:
            logger.warning(
                "Skipping recommendation: id %s not found in repository",
                item.restaurant_id,
            )
            continue
        _try_append(restaurant, item.explanation)

    if candidates and prefs and len(enriched) < top_k:
        for restaurant in candidates:
            if len(enriched) >= top_k:
                break
            _try_append(restaurant, _template_backfill_explanation(restaurant, prefs))

    return _rerank_by_preference_fit(enriched, prefs, top_k)


def _rerank_by_preference_fit(
    recommendations: list[RankedRecommendation],
    prefs: UserPreferences,
    top_k: int,
) -> list[RankedRecommendation]:
    """Re-order LLM picks so cuisine/budget fit wins over weak multi-cuisine matches."""
    if not recommendations or prefs is None or not prefs.cuisine:
        return recommendations

    def _fit_key(rec: RankedRecommendation) -> tuple:
        cuisines = [c.strip() for c in rec.cuisine.split(",") if c.strip()]
        pseudo = Restaurant(
            id=rec.restaurant_id,
            name=rec.name,
            location=rec.location,
            locality=rec.locality,
            cuisines=cuisines,
            rating=rec.rating,
            approx_cost=rec.approx_cost,
        )
        return (-cuisine_match_score(pseudo, prefs.cuisine), -(rec.rating or -1.0))

    ordered = sorted(recommendations, key=_fit_key)[:top_k]
    return [
        rec.model_copy(update={"rank": i})
        for i, rec in enumerate(ordered, start=1)
    ]


def _empty_response(
    *,
    filters_applied: dict[str, Any],
    total_matched: int,
    filter_duration_ms: float | None,
    message: str,
    suggestions: list[str],
) -> RecommendationResponse:
    return RecommendationResponse(
        success=True,
        summary=None,
        recommendations=[],
        message=message,
        suggestions=suggestions,
        metadata=ResponseMetadata(
            candidate_count=0,
            total_matched=total_matched,
            filters_applied=filters_applied,
            filter_duration_ms=filter_duration_ms,
            degraded_mode=False,
        ),
    )


def _error_response(
    message: str,
    *,
    filters_applied: dict[str, Any] | None = None,
    candidate_count: int = 0,
    total_matched: int = 0,
) -> RecommendationResponse:
    return RecommendationResponse(
        success=False,
        recommendations=[],
        message=message,
        metadata=ResponseMetadata(
            candidate_count=candidate_count,
            total_matched=total_matched,
            filters_applied=filters_applied or {},
            degraded_mode=False,
        ),
    )


class RecommendationOrchestrator:
    """Coordinates filter → LLM → enrich for a single recommendation request."""

    def __init__(
        self,
        repository: RestaurantRepository | None = None,
        engine: RecommendationEngine | None = None,
        *,
        llm_client: RecommendationLLM | None = None,
    ) -> None:
        self._repository = repository or RestaurantRepository()
        self._llm_client = llm_client
        self._engine = engine or RecommendationEngine(client=llm_client)

    def get_recommendations(
        self,
        prefs: UserPreferences,
        *,
        fail_without_api_key: bool = True,
        validate_location: bool = True,
    ) -> RecommendationResponse:
        """
        Run the full pipeline and return a UI-ready response.

        Empty filter results short-circuit before any LLM call (FLT-01).
        """
        settings = get_settings()

        try:
            if not self._repository.is_loaded:
                self._repository.load()

            if validate_location:
                validate_preferences(
                    prefs,
                    self._repository.get_available_locations(),
                )

            filter_start = time.perf_counter()
            filter_result = self._repository.filter(
                prefs,
                validate_location=False,
            )
            filter_duration_ms = (time.perf_counter() - filter_start) * 1000

            logger.info(
                "Filter completed: matched=%s candidates=%s duration_ms=%.1f",
                filter_result.total_matched,
                len(filter_result.candidates),
                filter_duration_ms,
            )

            if filter_result.is_empty or not filter_result.should_call_llm:
                return _empty_response(
                    filters_applied=filter_result.filters_applied,
                    total_matched=filter_result.total_matched,
                    filter_duration_ms=filter_duration_ms,
                    message=filter_result.message or "No restaurants match your criteria.",
                    suggestions=list(filter_result.suggestions),
                )

            candidates = filter_result.candidates
            candidate_count = len(candidates)

            if fail_without_api_key and self._llm_client is None:
                if not settings.groq_api_key or not str(settings.groq_api_key).strip():
                    return _error_response(
                        MISSING_API_KEY_MESSAGE,
                        filters_applied=filter_result.filters_applied,
                        candidate_count=candidate_count,
                        total_matched=filter_result.total_matched,
                    )

            system_prompt, user_prompt = build_prompts(candidates, prefs)
            token_estimate = estimate_prompt_tokens(system_prompt, user_prompt)
            logger.info("Prompt token estimate: ~%s", token_estimate)

            llm_start = time.perf_counter()
            try:
                llm_output = self._engine.rank_and_explain(candidates, prefs)
            except Exception as exc:
                logger.exception("LLM stage failed: %s", exc)
                from src.llm.parser import build_fallback_output

                llm_output = build_fallback_output(
                    candidates,
                    prefs,
                    top_k=settings.top_k_results,
                )
            llm_duration_ms = (time.perf_counter() - llm_start) * 1000

            enriched = _enrich_recommendations(
                llm_output,
                self._repository,
                candidates=candidates,
                prefs=prefs,
                top_k=settings.top_k_results,
            )

            logger.info(
                "LLM completed: results=%s degraded=%s duration_ms=%.1f",
                len(enriched),
                llm_output.degraded_mode,
                llm_duration_ms,
            )

            message = LLM_ERROR_MESSAGE if llm_output.degraded_mode else None

            return RecommendationResponse(
                success=True,
                summary=llm_output.summary,
                recommendations=enriched,
                message=message,
                metadata=ResponseMetadata(
                    candidate_count=candidate_count,
                    total_matched=filter_result.total_matched,
                    filters_applied=filter_result.filters_applied,
                    filter_duration_ms=filter_duration_ms,
                    llm_duration_ms=llm_duration_ms,
                    prompt_token_estimate=token_estimate,
                    degraded_mode=llm_output.degraded_mode,
                ),
            )

        except ValueError as exc:
            logger.warning("Validation error: %s", exc)
            return _error_response(str(exc))
        except Exception as exc:
            logger.exception("Filter/orchestration failed: %s", exc)
            return _error_response(FILTER_ERROR_MESSAGE)


def get_recommendations(
    prefs: UserPreferences,
    *,
    repository: RestaurantRepository | None = None,
    llm_client: RecommendationLLM | None = None,
    fail_without_api_key: bool = True,
    validate_location: bool = True,
) -> RecommendationResponse:
    """Convenience entry point for the full recommendation pipeline."""
    orchestrator = RecommendationOrchestrator(
        repository=repository,
        llm_client=llm_client,
    )
    return orchestrator.get_recommendations(
        prefs,
        fail_without_api_key=fail_without_api_key,
        validate_location=validate_location,
    )
