#!/usr/bin/env python3
"""Phase 1 smoke test: repository load, counts, Hyderabad filter."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.repository import RestaurantRepository


def main() -> int:
    repo = RestaurantRepository()
    print("Loading repository...")
    repo.load()

    total = repo.count()
    locations = repo.get_available_locations()
    bands = repo.get_budget_bands()

    print(f"Total restaurants: {total:,}")
    print(f"Unique cities:     {len(locations)}")
    print(f"Sample cities:     {locations[:10]}")
    print(f"Budget bands:      {bands.describe()}")

    sample = repo.get_all()[0]
    print("\nSample restaurant:")
    print(f"  id={sample.id} name={sample.name!r} city={sample.location!r}")
    print(f"  rating={sample.rating} cost={sample.approx_cost} cuisines={sample.cuisines[:3]}")

    bangalore = repo.filter_by_location("Bangalore")
    print(f"\nBangalore filter: {len(bangalore)} restaurants")

    if total < 8_000:
        print("WARNING: Expected ~8.7k clean rows; cache may be incomplete.")
        return 1
    if len(bangalore) == 0:
        print("FAIL: Bangalore filter returned no results.")
        return 1

    print("\nPhase 1 smoke test PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
