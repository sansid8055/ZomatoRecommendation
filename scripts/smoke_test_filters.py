#!/usr/bin/env python3
"""Phase 2 smoke test: full filter pipeline on cached data."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.models import UserPreferences
from src.data.repository import RestaurantRepository


def main() -> int:
    repo = RestaurantRepository()
    repo.load()

    # Bangalore + Italian + medium + rating 4+ (dataset is Bangalore-centric)
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = repo.filter(prefs)

    print("Phase 2 filter smoke test")
    print(f"  Total matched: {result.total_matched}")
    print(f"  Candidates:    {len(result.candidates)}")
    print(f"  Duration:      {result.duration_ms:.1f} ms")
    print(f"  Should call LLM: {result.should_call_llm}")

    if result.is_empty:
        print("FAIL: Expected non-empty result for Bangalore + Italian + medium")
        return 1

    if len(result.candidates) > 25:
        print("FAIL: Candidates exceed MAX_CANDIDATES")
        return 1

    for r in result.candidates:
        if r.location.lower() != "bangalore":
            print(f"FAIL: Candidate {r.name} not in Bangalore")
            return 1
        if r.rating is not None and r.rating < 4.0:
            print(f"FAIL: Rating below min_rating for {r.name}")
            return 1

    # Zero-match path
    empty = repo.filter(
        UserPreferences(
            location="Delhi",
            budget="medium",
            cuisine="Martian",
            min_rating=5.0,
        ),
        validate_location=False,
    )
    if not empty.is_empty or empty.should_call_llm:
        print("FAIL: Delhi+Martian should be empty without LLM")
        return 1

    print("\nPhase 2 smoke test PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
