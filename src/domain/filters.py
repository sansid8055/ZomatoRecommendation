"""
Candidate filter engine — deterministic narrowing before LLM (Phase 2).

Pipeline: location → rating → cuisine → budget → sort & cap.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from src.config.settings import get_settings
from src.data.models import Restaurant, UserPreferences
from src.domain.budget import BudgetBands, cost_in_budget

logger = logging.getLogger(__name__)

EMPTY_STATE_MESSAGE = (
    "No restaurants match your criteria in our dataset."
)

EMPTY_STATE_SUGGESTIONS = [
    "Lowering the minimum rating",
    "Choosing a broader cuisine (or leave blank)",
    "Switching budget to medium or high",
    "Picking a larger city from the list",
]


@dataclass(frozen=True)
class FilterCriteria:
    """Normalized filter inputs (subset of UserPreferences used for filtering)."""

    location: str
    budget: str
    cuisine: str | None = None
    min_rating: float | None = None

    @classmethod
    def from_preferences(cls, prefs: UserPreferences) -> FilterCriteria:
        return cls(
            location=prefs.location,
            budget=prefs.budget,
            cuisine=prefs.cuisine,
            min_rating=prefs.min_rating,
        )


@dataclass
class FilterResult:
    """Output of the filter pipeline."""

    candidates: list[Restaurant]
    total_matched: int
    is_empty: bool
    message: str | None = None
    suggestions: list[str] = field(default_factory=list)
    filters_applied: dict[str, object] = field(default_factory=dict)
    duration_ms: float | None = None

    @property
    def should_call_llm(self) -> bool:
        return not self.is_empty and len(self.candidates) > 0


def validate_preferences(
    prefs: UserPreferences,
    available_locations: list[str] | None = None,
) -> UserPreferences:
    """
    Validate and normalize preferences.
    Raises ValueError on invalid input.
    """
    if not prefs.location or not prefs.location.strip():
        raise ValueError("Please select a location.")

    if prefs.budget not in ("low", "medium", "high"):
        raise ValueError("Invalid budget value. Use low, medium, or high.")

    if available_locations:
        loc_lower = prefs.location.strip().lower()
        known = {loc.lower() for loc in available_locations}
        if loc_lower not in known:
            # Allow substring match (e.g. user typed partial area name)
            if not any(loc_lower in k or k in loc_lower for k in known):
                preferred = next(
                    (m for m in ("Bangalore", "Hyderabad", "Delhi", "Mumbai") if m in available_locations),
                    None,
                )
                sample = preferred or ", ".join(available_locations[:5])
                raise ValueError(
                    f"Location not found. Choose from the list (e.g. {sample})."
                )

    return prefs


def _matches_location(restaurant: Restaurant, location: str) -> bool:
    needle = location.strip().lower()
    if not needle:
        return False
    loc = restaurant.location.lower()
    if loc == needle or needle in loc:
        return True
    if restaurant.locality:
        locality = restaurant.locality.lower()
        if locality == needle or needle in locality:
            return True
    return False


def _matches_rating(restaurant: Restaurant, min_rating: float | None) -> bool:
    if min_rating is None or min_rating <= 0:
        return True
    if restaurant.rating is None:
        return False
    return restaurant.rating >= min_rating


def cuisine_match_score(restaurant: Restaurant, cuisine: str | None) -> int:
    """
    Relevance score when user requests a cuisine (higher = better match).

    3 = sole/primary cuisine (first token exact match)
    2 = exact token elsewhere in list
    1 = substring match (e.g. 'North Indian' contains 'indian')
    0 = no cuisine filter / not applicable
    -1 = no match (should not appear after filter)
    """
    if not cuisine or not cuisine.strip():
        return 0

    query = cuisine.strip().lower()
    if len(query) < 2:
        return 0

    tokens = [c.strip().lower() for c in restaurant.cuisines if c and str(c).strip()]
    if not tokens:
        return -1

    if tokens[0] == query or (len(tokens) == 1 and tokens[0] == query):
        return 3
    if query in tokens:
        return 2
    for token in tokens:
        if len(query) >= 3 and query in token:
            return 1
    return -1


def _matches_cuisine(restaurant: Restaurant, cuisine: str | None) -> bool:
    if not cuisine or not cuisine.strip():
        return True
    return cuisine_match_score(restaurant, cuisine) >= 1


def _matches_budget(
    restaurant: Restaurant,
    budget: str,
    bands: BudgetBands,
) -> bool:
    return cost_in_budget(restaurant.approx_cost, budget, bands)


def _sort_key(restaurant: Restaurant) -> tuple[float, int, str]:
    rating = restaurant.rating if restaurant.rating is not None else -1.0
    votes = restaurant.votes if restaurant.votes is not None else 0
    return (-rating, -votes, restaurant.id)


def _rank_key(restaurant: Restaurant, criteria: FilterCriteria) -> tuple:
    """Sort: cuisine fit (if requested), then rating, votes, stable id."""
    cuisine_score = cuisine_match_score(restaurant, criteria.cuisine)
    rating = restaurant.rating if restaurant.rating is not None else -1.0
    votes = restaurant.votes if restaurant.votes is not None else 0
    return (-cuisine_score, -rating, -votes, restaurant.id)


def restaurant_dedupe_key(restaurant: Restaurant) -> tuple[str, str, str]:
    """
    Identity key for chain/branch duplicates in the HF dataset (DAT-04).

    Same name + metro + locality often appears as multiple rows with different URLs/IDs.
    """
    return (
        restaurant.name.strip().lower(),
        restaurant.location.strip().lower(),
        (restaurant.locality or "").strip().lower(),
    )


def dedupe_restaurants(restaurants: list[Restaurant]) -> list[Restaurant]:
    """
    Keep the best-rated row per dedupe key; preserve input order among kept rows.

    Call after sorting by `_sort_key` so the first row per key is the best match.
    """
    seen: set[tuple[str, str, str]] = set()
    unique: list[Restaurant] = []
    for restaurant in restaurants:
        key = restaurant_dedupe_key(restaurant)
        if key in seen:
            continue
        seen.add(key)
        unique.append(restaurant)
    return unique


def apply_filters(
    restaurants: list[Restaurant],
    criteria: FilterCriteria,
    bands: BudgetBands,
    *,
    max_candidates: int | None = None,
) -> FilterResult:
    """Run full filter pipeline and return capped candidate list."""
    settings = get_settings()
    cap = max_candidates if max_candidates is not None else settings.max_candidates

    start = time.perf_counter()
    matched: list[Restaurant] = list(restaurants)

    matched = [r for r in matched if _matches_location(r, criteria.location)]
    matched = [r for r in matched if _matches_rating(r, criteria.min_rating)]
    matched = [r for r in matched if _matches_cuisine(r, criteria.cuisine)]
    matched = [r for r in matched if _matches_budget(r, criteria.budget, bands)]

    total_matched = len(matched)
    matched.sort(key=lambda r: _rank_key(r, criteria))
    matched = dedupe_restaurants(matched)
    candidates = matched[:cap]

    duration_ms = (time.perf_counter() - start) * 1000
    if duration_ms > 200:
        logger.warning("Filter pipeline took %.1f ms (target < 200 ms)", duration_ms)

    filters_applied = {
        "location": criteria.location,
        "budget": criteria.budget,
        "cuisine": criteria.cuisine,
        "min_rating": criteria.min_rating,
        "max_candidates": cap,
    }

    if not candidates:
        return FilterResult(
            candidates=[],
            total_matched=0,
            is_empty=True,
            message=EMPTY_STATE_MESSAGE,
            suggestions=list(EMPTY_STATE_SUGGESTIONS),
            filters_applied=filters_applied,
            duration_ms=duration_ms,
        )

    return FilterResult(
        candidates=candidates,
        total_matched=total_matched,
        is_empty=False,
        filters_applied=filters_applied,
        duration_ms=duration_ms,
    )


def filter_preferences(
    restaurants: list[Restaurant],
    prefs: UserPreferences,
    bands: BudgetBands,
    *,
    available_locations: list[str] | None = None,
    max_candidates: int | None = None,
) -> FilterResult:
    """Validate preferences and apply filters."""
    validate_preferences(prefs, available_locations)
    criteria = FilterCriteria.from_preferences(prefs)
    return apply_filters(
        restaurants,
        criteria,
        bands,
        max_candidates=max_candidates,
    )


def _print_filter_probe(result: FilterResult, *, location: str, budget: str, cuisine: str | None, min_rating: float | None) -> None:
    print(f"Location:     {location}")
    print(f"Budget:       {budget}")
    print(f"Cuisine:      {cuisine or '(any)'}")
    print(f"Min rating:   {min_rating if min_rating is not None else '(any)'}")
    print(f"Total matched:{result.total_matched}")
    print(f"Candidates:   {len(result.candidates)} (capped)")
    if result.duration_ms is not None:
        print(f"Duration:     {result.duration_ms:.1f} ms")
    print(f"Call LLM:     {result.should_call_llm}")

    if result.is_empty:
        print(f"\n{result.message}")
        for tip in result.suggestions:
            print(f"  • {tip}")
        return

    print("\nTop results:")
    for i, r in enumerate(result.candidates[:5], 1):
        cuisines = ", ".join(r.cuisines[:2]) if r.cuisines else ""
        print(
            f"  {i}. {r.name} | {r.location} | "
            f"rating={r.rating} cost={r.approx_cost} | {cuisines}"
        )


def main(argv: list[str] | None = None) -> int:
    """CLI probe: python -m src.domain.filters --location Delhi --budget medium"""
    import argparse

    from src.data.repository import RestaurantRepository

    parser = argparse.ArgumentParser(description="Probe restaurant filter pipeline (Phase 2)")
    parser.add_argument("--location", required=True, help="City or area from dataset")
    parser.add_argument("--budget", required=True, choices=["low", "medium", "high"])
    parser.add_argument("--cuisine", default=None, help="Optional cuisine filter")
    parser.add_argument("--min-rating", type=float, default=None, dest="min_rating")
    parser.add_argument(
        "--no-validate-location",
        action="store_true",
        help="Skip location whitelist check (for edge-case probes)",
    )
    args = parser.parse_args(argv)

    prefs = UserPreferences(
        location=args.location,
        budget=args.budget,
        cuisine=args.cuisine,
        min_rating=args.min_rating,
    )

    repo = RestaurantRepository()
    repo.load()
    if args.no_validate_location:
        criteria = FilterCriteria.from_preferences(prefs)
        result = apply_filters(repo.get_all(), criteria, repo.get_budget_bands())
    else:
        result = repo.filter(prefs)

    _print_filter_probe(
        result,
        location=args.location,
        budget=args.budget,
        cuisine=args.cuisine,
        min_rating=args.min_rating,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
