"""Parse and validate LLM JSON responses."""

from __future__ import annotations

import json
import logging
import re

from src.data.models import Restaurant, UserPreferences
from src.llm.models import LLMRecommendationItem, LLMRecommendationOutput

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def extract_json_text(raw: str) -> str:
    """Strip markdown fences and surrounding whitespace."""
    text = raw.strip()
    match = _JSON_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_llm_response(
    raw: str,
    valid_ids: set[str],
    *,
    top_k: int = 5,
) -> LLMRecommendationOutput:
    """
    Parse LLM JSON, validate restaurant IDs, dedupe, and cap to top_k.
    Raises ValueError on unrecoverable parse errors.
    """
    text = extract_json_text(raw)
    data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object")

    summary = data.get("summary")
    if summary is not None:
        summary = str(summary).strip() or None

    raw_items = data.get("recommendations")
    if not isinstance(raw_items, list):
        raise ValueError("Missing or invalid 'recommendations' array")

    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    items: list[LLMRecommendationItem] = []

    for entry in raw_items:
        if not isinstance(entry, dict):
            continue
        rid = str(entry.get("restaurant_id", "")).strip()
        if not rid or rid not in valid_ids:
            if rid:
                logger.warning("Dropped hallucinated restaurant_id: %s", rid)
            continue
        if rid in seen_ids:
            continue

        try:
            rank = int(entry.get("rank", len(items) + 1))
        except (TypeError, ValueError):
            rank = len(items) + 1

        explanation = str(entry.get("explanation", "")).strip()
        if not explanation:
            explanation = "Matches your search preferences."

        seen_ids.add(rid)
        if rank in seen_ranks:
            rank = len(items) + 1
        seen_ranks.add(rank)

        items.append(
            LLMRecommendationItem(
                restaurant_id=rid,
                rank=rank,
                explanation=explanation,
            )
        )

    items.sort(key=lambda x: x.rank)
    items = items[:top_k]
    items = [
        LLMRecommendationItem(
            restaurant_id=item.restaurant_id,
            rank=i,
            explanation=item.explanation,
        )
        for i, item in enumerate(items, start=1)
    ]

    return LLMRecommendationOutput(summary=summary, recommendations=items)


def build_fallback_output(
    candidates: list[Restaurant],
    prefs: UserPreferences,
    *,
    top_k: int = 5,
) -> LLMRecommendationOutput:
    """Rule-based ranking when LLM fails (degraded mode)."""
    from src.domain.filters import dedupe_restaurants

    sorted_candidates = sorted(
        candidates,
        key=lambda r: (
            -(r.rating if r.rating is not None else -1.0),
            -(r.votes if r.votes is not None else 0),
        ),
    )
    sorted_candidates = dedupe_restaurants(sorted_candidates)[:top_k]

    cuisine_part = f" {prefs.cuisine}" if prefs.cuisine else ""
    summary = (
        f"Top-rated{cuisine_part} options in {prefs.location} "
        f"for your {prefs.budget} budget (AI ranking unavailable)."
    )

    recommendations: list[LLMRecommendationItem] = []
    for i, r in enumerate(sorted_candidates, start=1):
        rating_text = f"{r.rating} stars" if r.rating is not None else "well-reviewed"
        cost_text = (
            f"₹{r.approx_cost} for two" if r.approx_cost else "reasonable pricing"
        )
        explanation = (
            f"{r.name} is highly rated in {prefs.location} with {rating_text}, "
            f"fitting your {prefs.budget} budget ({cost_text})."
        )
        if prefs.cuisine and any(
            prefs.cuisine.lower() in c.lower() for c in r.cuisines
        ):
            explanation += f" Serves {prefs.cuisine} cuisine."

        recommendations.append(
            LLMRecommendationItem(
                restaurant_id=r.id,
                rank=i,
                explanation=explanation,
            )
        )

    return LLMRecommendationOutput(
        summary=summary,
        recommendations=recommendations,
        degraded_mode=True,
    )
