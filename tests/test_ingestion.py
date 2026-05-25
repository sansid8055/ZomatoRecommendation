import pandas as pd

from src.data.ingestion import (
    _parse_cost,
    _parse_cuisines,
    _parse_rating,
    _normalize_city,
    transform_dataframe,
)
from src.domain.budget import compute_budget_bands, cost_in_budget


def test_parse_rating_formats():
    assert _parse_rating("4.1/5") == 4.1
    assert _parse_rating("NEW") is None
    assert _parse_rating("-") is None
    assert _parse_rating(4.5) == 4.5


def test_parse_cost_formats():
    assert _parse_cost("1,200") == 1200
    assert _parse_cost("800") == 800
    assert _parse_cost("-") is None
    assert _parse_cost(0) is None


def test_parse_cuisines_split():
    assert _parse_cuisines("North Indian, Chinese, Italian") == [
        "North Indian",
        "Chinese",
        "Italian",
    ]


def test_normalize_city_aliases():
    assert _normalize_city("bengaluru") == "Bangalore"
    assert _normalize_city("New Delhi") == "Delhi"


def test_transform_minimal_dataframe():
    raw = pd.DataFrame(
        [
            {
                "url": "https://zomato.com/r/1",
                "name": "Test Cafe",
                "location": "Koramangala",
                "listed_in(city)": "Bangalore",
                "cuisines": "Chinese, Italian",
                "rate": "4.2/5",
                "approx_cost(for two people)": "600",
                "votes": 100,
                "address": "123 Main St, Koramangala, Bangalore",
                "rest_type": "Casual Dining",
            }
        ]
    )
    clean, bands = transform_dataframe(raw)
    assert len(clean) == 1
    assert clean.iloc[0]["location"] == "Bangalore"
    assert clean.iloc[0]["rating"] == 4.2
    assert clean.iloc[0]["approx_cost"] == 600
    assert "Chinese" in clean.iloc[0]["cuisines"]

    assert cost_in_budget(600, "medium", bands) in (True, False)


def test_budget_bands_from_series():
    costs = pd.Series([100, 200, 300, 400, 500, 600, 700, 800, 900])
    bands = compute_budget_bands(costs)
    assert bands.low_max < bands.high_min
