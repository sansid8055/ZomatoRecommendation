from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.data.repository import RestaurantRepository


@pytest.fixture
def parquet_path() -> Path | None:
    path = get_settings().data_cache_path
    return path if path.exists() else None


@pytest.mark.skipif(
    not get_settings().data_cache_path.exists(),
    reason="Parquet cache not built; run scripts/download_dataset.py",
)
def test_repository_load_and_bangalore_filter():
    repo = RestaurantRepository()
    repo.load()
    assert repo.count() >= 8000  # Bangalore dataset from ManikaSaini/zomato-restaurant-recommendation
    bangalore = repo.filter_by_location("Bangalore")
    assert len(bangalore) > 0
    assert all(
        r.location.lower() == "bangalore" or "bangalore" in r.location.lower()
        for r in bangalore[:20]
    )
