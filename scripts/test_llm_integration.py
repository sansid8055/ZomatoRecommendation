#!/usr/bin/env python3
"""
Phase 3 LLM integration test.

Default: mock client (no API key).
Use --live for Groq API (requires GROQ_API_KEY in .env).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.models import UserPreferences
from src.data.repository import RestaurantRepository
from src.llm.client import ConfigurationError, MockLLMClient, get_llm_client
from src.llm.engine import RecommendationEngine


def main() -> int:
    parser = argparse.ArgumentParser(description="Test LLM ranking pipeline")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call real Groq API (requires GROQ_API_KEY in .env)",
    )
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    repo = RestaurantRepository()
    repo.load()

    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    filter_result = repo.filter(prefs)
    candidates = filter_result.candidates[:10]

    if not candidates:
        print("No candidates from filter; cannot test LLM.")
        return 1

    print(f"Candidates for LLM: {len(candidates)}")
    print(f"Mode: {'live Groq' if args.live else 'mock'}")

    if args.live:
        try:
            client = get_llm_client(use_mock=False)
        except ConfigurationError as exc:
            print(f"Configuration error: {exc}")
            return 1
    else:
        client = MockLLMClient(candidates, top_k=args.top_k)

    engine = RecommendationEngine(client=client)
    result = engine.rank_and_explain(candidates, prefs, top_k=args.top_k)

    print(f"\nDegraded mode: {result.degraded_mode}")
    if result.summary:
        print(f"Summary: {result.summary[:200]}")
    print(f"Recommendations: {len(result.recommendations)}")

    valid_ids = {c.id for c in candidates}
    for item in result.recommendations:
        ok = item.restaurant_id in valid_ids
        print(
            f"  #{item.rank} id={item.restaurant_id} valid={ok} | "
            f"{item.explanation[:80]}..."
        )
        if not ok:
            print("FAIL: hallucinated ID")
            return 1

    if len(result.recommendations) < 1:
        print("FAIL: no recommendations returned")
        return 1

    print("\nPhase 3 LLM integration test PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
