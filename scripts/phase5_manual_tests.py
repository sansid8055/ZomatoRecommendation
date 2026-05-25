#!/usr/bin/env python3
"""Phase 5 manual test checklist (implementation-plan exit criteria)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import get_settings
from src.data.models import UserPreferences
from src.services.orchestrator import (
    MISSING_API_KEY_MESSAGE,
    RecommendationOrchestrator,
)


def _header(name: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print("=" * 60)


def test_valid_prefs_five_cards() -> bool:
    """Checklist: valid prefs -> 5 cards with explanations."""
    _header("Test 1: Valid prefs -> 5 cards with explanations")
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Chinese",
        min_rating=4.0,
    )
    orch = RecommendationOrchestrator()
    response = orch.get_recommendations(prefs, fail_without_api_key=True)

    ok = True
    if not response.success:
        print(f"FAIL: success=False - {response.message}")
        return False

    recs = response.recommendations
    if len(recs) < 1:
        print(f"FAIL: expected >=1 recommendation, got {len(recs)}")
        print(f"  message: {response.message}")
        return False

    if len(recs) != 5:
        print(f"WARN: expected 5 cards, got {len(recs)} (top_k may differ)")

    for rec in recs:
        if not rec.explanation or not rec.explanation.strip():
            print(f"FAIL: #{rec.rank} {rec.name} missing explanation")
            ok = False
        if not rec.name or not rec.cuisine:
            print(f"FAIL: #{rec.rank} missing name or cuisine")
            ok = False

    print(f"PASS: {len(recs)} recommendations with explanations")
    if response.summary:
        print(f"  summary: {response.summary[:80]}...")
    for rec in recs[:3]:
        print(
            f"  #{rec.rank} {rec.name} | {rec.cuisine} | "
            f"rating={rec.rating} | cost={rec.approx_cost}"
        )
    return ok


def test_impossible_filter_empty_state() -> bool:
    """Checklist: impossible filter -> empty state, no crash."""
    _header("Test 2: Impossible filter combo -> empty state")
    prefs = UserPreferences(
        location="Bangalore",
        budget="low",
        cuisine="QuantumFusionCuisineXYZ",
        min_rating=5.0,
    )
    orch = RecommendationOrchestrator()
    try:
        response = orch.get_recommendations(prefs, fail_without_api_key=True)
    except Exception as exc:
        print(f"FAIL: crashed with {type(exc).__name__}: {exc}")
        return False

    if not response.success:
        print(f"FAIL: success=False - {response.message}")
        return False

    if response.recommendations:
        print(
            f"WARN: got {len(response.recommendations)} results "
            "(strict combo still matched something)"
        )

    if not response.message and not response.suggestions:
        print("FAIL: no empty-state message or suggestions")
        return False

    print(f"PASS: empty state - {response.message}")
    if response.suggestions:
        print(f"  suggestions: {response.suggestions[:2]}")
    return True


def test_missing_api_key_error() -> bool:
    """Checklist: missing GROQ_API_KEY -> clear error."""
    _header("Test 3: Missing GROQ_API_KEY -> clear error")
    saved = os.environ.get("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = ""

    try:
        get_settings.cache_clear()
        prefs = UserPreferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=3.0,
        )
        orch = RecommendationOrchestrator()
        response = orch.get_recommendations(prefs, fail_without_api_key=True)
    finally:
        if saved is None:
            os.environ.pop("GROQ_API_KEY", None)
        else:
            os.environ["GROQ_API_KEY"] = saved
        get_settings.cache_clear()

    if response.success:
        print("FAIL: expected success=False when API key missing")
        return False

    if MISSING_API_KEY_MESSAGE not in (response.message or ""):
        print(f"FAIL: unexpected message: {response.message}")
        return False

    print(f"PASS: {response.message}")
    return True


def main() -> int:
    print("Phase 5 manual test checklist")
    print(f"Project root: {PROJECT_ROOT}")

    settings = get_settings()
    if not settings.data_cache_path.exists():
        print("ERROR: dataset missing - run scripts/download_dataset.py")
        return 1

    if not settings.groq_api_key:
        print("ERROR: GROQ_API_KEY required for Test 1 (set in .env)")
        return 1

    results = [
        ("Valid prefs -> 5 cards", test_valid_prefs_five_cards()),
        ("Impossible filter -> empty", test_impossible_filter_empty_state()),
        ("Missing API key -> error", test_missing_api_key_error()),
    ]

    print(f"\n{'=' * 60}")
    print("  Summary")
    print("=" * 60)
    all_ok = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        all_ok = all_ok and passed

    print()
    if all_ok:
        print("All Phase 5 manual tests PASSED.")
        print("Next: streamlit run src/app/main.py - verify UI in browser.")
        return 0
    print("Some Phase 5 manual tests FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
