#!/usr/bin/env python3
"""Phase 4 CLI: run full recommendation pipeline from the terminal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.models import UserPreferences
from src.llm.client import MockLLMClient
from src.services.orchestrator import RecommendationOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Get restaurant recommendations (filter → LLM → enrich)",
    )
    parser.add_argument("--location", required=True)
    parser.add_argument("--budget", required=True, choices=["low", "medium", "high"])
    parser.add_argument("--cuisine", default=None)
    parser.add_argument("--min-rating", type=float, default=None, dest="min_rating")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use MockLLMClient (no Groq API call)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full RecommendationResponse as JSON",
    )
    args = parser.parse_args()

    prefs = UserPreferences(
        location=args.location,
        budget=args.budget,
        cuisine=args.cuisine,
        min_rating=args.min_rating,
    )

    orchestrator = RecommendationOrchestrator()
    if args.mock:
        if not orchestrator._repository.is_loaded:
            orchestrator._repository.load()
        filtered = orchestrator._repository.filter(prefs)
        mock = MockLLMClient(filtered.candidates, top_k=5)
        orchestrator = RecommendationOrchestrator(
            repository=orchestrator._repository,
            llm_client=mock,
        )

    response = orchestrator.get_recommendations(
        prefs,
        fail_without_api_key=not args.mock,
    )

    if args.json:
        print(response.model_dump_json(indent=2))
    else:
        print(f"Success:       {response.success}")
        print(f"Candidates:    {response.metadata.candidate_count}")
        print(f"Total matched: {response.metadata.total_matched}")
        print(f"Degraded:      {response.metadata.degraded_mode}")
        if response.message:
            print(f"Message:       {response.message}")
        if response.summary:
            print(f"\nSummary:\n{response.summary}\n")
        if not response.recommendations:
            for tip in response.suggestions:
                print(f"  • {tip}")
        else:
            print("Recommendations:")
            for rec in response.recommendations:
                cost = f"INR {rec.approx_cost}" if rec.approx_cost else "N/A"
                rating = rec.rating if rec.rating is not None else "N/A"
                print(
                    f"  #{rec.rank} {rec.name} | {rec.cuisine} | "
                    f"rating={rating} | {cost} | {rec.location}"
                )
                print(f"     {rec.explanation[:120]}...")

    return 0 if response.success and (response.recommendations or response.message) else 1


if __name__ == "__main__":
    raise SystemExit(main())
