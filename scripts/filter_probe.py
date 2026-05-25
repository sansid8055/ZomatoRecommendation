#!/usr/bin/env python3
"""CLI probe for Phase 2 filter pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.models import UserPreferences
from src.data.repository import RestaurantRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe restaurant filters")
    parser.add_argument("--location", required=True, help="City or area")
    parser.add_argument(
        "--budget",
        required=True,
        choices=["low", "medium", "high"],
    )
    parser.add_argument("--cuisine", default=None, help="Cuisine filter (optional)")
    parser.add_argument("--min-rating", type=float, default=None, dest="min_rating")
    args = parser.parse_args()

    prefs = UserPreferences(
        location=args.location,
        budget=args.budget,
        cuisine=args.cuisine,
        min_rating=args.min_rating,
    )

    repo = RestaurantRepository()
    repo.load()
    result = repo.filter(prefs)

    print(f"Location:     {args.location}")
    print(f"Budget:       {args.budget}")
    print(f"Cuisine:      {args.cuisine or '(any)'}")
    print(f"Min rating:   {args.min_rating if args.min_rating else '(any)'}")
    print(f"Total matched:{result.total_matched}")
    print(f"Candidates:   {len(result.candidates)} (capped)")
    print(f"Duration:     {result.duration_ms:.1f} ms" if result.duration_ms else "")
    print(f"Call LLM:     {result.should_call_llm}")

    if result.is_empty:
        print(f"\n{result.message}")
        for tip in result.suggestions:
            print(f"  • {tip}")
        return 0

    print("\nTop results:")
    for i, r in enumerate(result.candidates[:5], 1):
        print(
            f"  {i}. {r.name} | {r.location} | "
            f"rating={r.rating} cost={r.approx_cost} | {', '.join(r.cuisines[:2])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
