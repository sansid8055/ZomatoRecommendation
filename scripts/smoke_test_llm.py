#!/usr/bin/env python3
"""Phase 3 smoke test: mock LLM on filtered candidates."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.models import UserPreferences
from src.data.repository import RestaurantRepository
from src.llm.client import MockLLMClient
from src.llm.engine import RecommendationEngine


def main() -> int:
    repo = RestaurantRepository()
    repo.load()

    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    filtered = repo.filter(prefs)
    candidates = filtered.candidates

    if len(candidates) < 1:
        print("FAIL: need candidates from filter")
        return 1

    # Use first 10 for smoke test
    candidates = candidates[:10]
    mock = MockLLMClient(candidates, top_k=5)
    engine = RecommendationEngine(client=mock)
    result = engine.rank_and_explain(candidates, prefs, top_k=5)

    valid_ids = {c.id for c in candidates}
    if result.degraded_mode:
        print("FAIL: unexpected degraded mode with mock client")
        return 1
    if len(result.recommendations) != 5:
        print(f"FAIL: expected 5 recommendations, got {len(result.recommendations)}")
        return 1
    for item in result.recommendations:
        if item.restaurant_id not in valid_ids:
            print(f"FAIL: invalid id {item.restaurant_id}")
            return 1
        if item.rank < 1 or item.rank > 5:
            print(f"FAIL: invalid rank {item.rank}")
            return 1

    print("Phase 3 smoke test PASSED.")
    print(f"  Candidates in:  {len(candidates)}")
    print(f"  Ranked out:     {len(result.recommendations)}")
    print(f"  Summary:        {(result.summary or '')[:80]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
