"""Prompt construction for grounded restaurant ranking."""

from __future__ import annotations

import json

from src.config.settings import get_settings
from src.data.models import Restaurant, UserPreferences

SYSTEM_PROMPT = """You are a restaurant recommendation assistant for a Zomato-style app.

RULES (strict):
1. Rank ONLY restaurants from the CANDIDATES list below. Never invent restaurants or IDs.
2. Every restaurant_id in your output MUST appear in the candidate list.
3. Return valid JSON only — no markdown, no extra text.
4. Explanations must reference the user's stated preferences (location, budget, cuisine, rating, extras).
5. If no candidate is a strong match, say so honestly in the explanation.
6. Each restaurant name may appear at most once in your recommendations (no duplicate chains).
7. When the user specifies a cuisine, rank restaurants where that cuisine is PRIMARY (listed first or the only cuisine) above places that only mention it as a secondary option.
8. Respect budget tier: prefer costs that fit the stated budget; do not recommend clearly mismatched price points unless no better option exists.

OUTPUT JSON schema:
{
  "summary": "1-2 sentence overview of the picks",
  "recommendations": [
    {
      "restaurant_id": "<id from candidates>",
      "rank": 1,
      "explanation": "Why this fits the user (2-3 sentences)"
    }
  ]
}

Rank from 1 (best) upward. Include at most TOP_K restaurants."""


def _candidate_payload(restaurant: Restaurant) -> dict:
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "location": restaurant.location,
        "locality": restaurant.locality,
        "cuisines": restaurant.cuisines,
        "rating": restaurant.rating,
        "approx_cost": restaurant.approx_cost,
        "votes": restaurant.votes,
        "rest_type": restaurant.rest_type,
    }


def _preferences_payload(prefs: UserPreferences) -> dict:
    payload = {
        "location": prefs.location,
        "budget": prefs.budget,
        "cuisine": prefs.cuisine,
        "min_rating": prefs.min_rating,
    }
    if prefs.additional_preferences:
        payload["additional_preferences"] = prefs.additional_preferences
    return payload


def build_prompts(
    candidates: list[Restaurant],
    prefs: UserPreferences,
    *,
    top_k: int | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt)."""
    settings = get_settings()
    k = top_k if top_k is not None else settings.top_k_results

    candidate_table = [_candidate_payload(r) for r in candidates]
    user_payload = {
        "user_preferences": _preferences_payload(prefs),
        "top_k": k,
        "candidates": candidate_table,
    }

    system = SYSTEM_PROMPT.replace("TOP_K", str(k))
    user = (
        "Rank the best restaurants for this user.\n\n"
        f"{json.dumps(user_payload, indent=2, ensure_ascii=False)}"
    )
    return system, user


def build_retry_user_prompt(original_user_prompt: str) -> str:
    """Stricter instruction when first JSON parse fails."""
    return (
        original_user_prompt
        + "\n\nIMPORTANT: Respond with JSON ONLY. No markdown code fences. "
        'Use exactly: {"summary": "...", "recommendations": [{"restaurant_id": "...", "rank": 1, "explanation": "..."}]}'
    )
