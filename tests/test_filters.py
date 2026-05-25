import pytest
from pydantic import ValidationError

from src.data.models import Restaurant, UserPreferences
from src.domain.budget import BudgetBands
from src.domain.filters import (
    FilterCriteria,
    apply_filters,
    cuisine_match_score,
    dedupe_restaurants,
    filter_preferences,
    restaurant_dedupe_key,
    validate_preferences,
    _matches_cuisine,
    _matches_location,
)


def _sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="1",
            name="Italian Place",
            location="Bangalore",
            locality="Koramangala",
            cuisines=["Italian", "Continental"],
            rating=4.5,
            approx_cost=600,
            votes=500,
        ),
        Restaurant(
            id="2",
            name="Budget Chinese",
            location="Bangalore",
            locality="BTM",
            cuisines=["Chinese"],
            rating=3.8,
            approx_cost=250,
            votes=200,
        ),
        Restaurant(
            id="3",
            name="Fine Dining",
            location="Bangalore",
            locality="Indiranagar",
            cuisines=["North Indian"],
            rating=4.9,
            approx_cost=1200,
            votes=800,
        ),
        Restaurant(
            id="4",
            name="No Rating Cafe",
            location="Bangalore",
            cuisines=["Cafe"],
            rating=None,
            approx_cost=520,
            votes=50,
        ),
        Restaurant(
            id="5",
            name="Delhi Diner",
            location="Delhi",
            cuisines=["Italian"],
            rating=4.2,
            approx_cost=550,
            votes=300,
        ),
    ]


@pytest.fixture
def bands() -> BudgetBands:
    # Align with sample restaurant costs (250–1200)
    return BudgetBands(low_max=500, medium_min=501, medium_max=1500, high_min=1501)


def test_dedupe_restaurants_keeps_best_rated_branch():
    dup_a = Restaurant(
        id="a",
        name="Chain Bistro",
        location="Bangalore",
        locality="Koramangala",
        cuisines=["Chinese"],
        rating=4.1,
        approx_cost=500,
        votes=100,
    )
    dup_b = Restaurant(
        id="b",
        name="Chain Bistro",
        location="Bangalore",
        locality="Koramangala",
        cuisines=["Chinese"],
        rating=4.5,
        approx_cost=520,
        votes=50,
    )
    other = Restaurant(
        id="c",
        name="Unique Place",
        location="Bangalore",
        cuisines=["Chinese"],
        rating=4.0,
        approx_cost=480,
        votes=80,
    )
    sorted_input = sorted([dup_a, dup_b, other], key=lambda r: (-(r.rating or 0), -(r.votes or 0)))
    result = dedupe_restaurants(sorted_input)
    assert len(result) == 2
    assert result[0].id == "b"
    assert restaurant_dedupe_key(dup_a) == restaurant_dedupe_key(dup_b)


def test_apply_filters_dedupes_before_cap(bands):
    branches = [
        Restaurant(
            id=str(i),
            name="Same Chain",
            location="Bangalore",
            locality="BTM",
            cuisines=["Chinese"],
            rating=4.0 + i * 0.01,
            approx_cost=600,
            votes=100,
        )
        for i in range(5)
    ]
    criteria = FilterCriteria(
        location="Bangalore",
        budget="medium",
        cuisine="Chinese",
        min_rating=4.0,
    )
    result = apply_filters(branches, criteria, bands, max_candidates=25)
    assert len(result.candidates) == 1
    assert result.candidates[0].name == "Same Chain"


def test_matches_location_city_and_locality():
    r = _sample_restaurants()[0]
    assert _matches_location(r, "Bangalore")
    assert _matches_location(r, "Koramangala")
    assert not _matches_location(r, "Delhi")


def test_matches_cuisine_token_and_case_insensitive():
    r = _sample_restaurants()[0]
    assert _matches_cuisine(r, "italian")
    assert _matches_cuisine(r, "Italian")
    assert not _matches_cuisine(r, "Mexican")


def test_cuisine_short_false_positive_avoided():
    r = Restaurant(
        id="x",
        name="Test",
        location="Bangalore",
        cuisines=["Chinese"],
        rating=4.0,
        approx_cost=300,
    )
    assert not _matches_cuisine(r, "sin")


def test_filter_location_only(bands):
    criteria = FilterCriteria(location="Bangalore", budget="medium")
    result = apply_filters(_sample_restaurants(), criteria, bands, max_candidates=25)
    assert not result.is_empty
    assert result.total_matched == 3  # medium budget in Bangalore (excludes low-cost rows)
    assert all(r.location == "Bangalore" for r in result.candidates)


def test_filter_rating_excludes_null(bands):
    criteria = FilterCriteria(
        location="Bangalore",
        budget="medium",
        min_rating=4.0,
    )
    result = apply_filters(_sample_restaurants(), criteria, bands, max_candidates=25)
    assert all(
        r.rating is not None and r.rating >= 4.0 for r in result.candidates
    )
    assert not any(r.name == "No Rating Cafe" for r in result.candidates)


def test_cuisine_match_score_prefers_primary_cuisine():
    primary = Restaurant(
        id="1",
        name="Green Onion",
        location="Bangalore",
        cuisines=["Chinese"],
        rating=4.3,
        approx_cost=550,
    )
    secondary = Restaurant(
        id="2",
        name="Biryani Plus",
        location="Bangalore",
        cuisines=["Biryani", "North Indian", "Chinese"],
        rating=4.3,
        approx_cost=550,
    )
    assert cuisine_match_score(primary, "Chinese") == 3
    assert cuisine_match_score(secondary, "Chinese") == 2


def test_filter_chinese_prefers_primary_cuisine_over_rating_tie(bands):
    primary = Restaurant(
        id="1",
        name="Green Onion",
        location="Bangalore",
        cuisines=["Chinese"],
        rating=4.2,
        approx_cost=550,
        votes=50,
    )
    multi = Restaurant(
        id="2",
        name="Wok Paper Scissors",
        location="Bangalore",
        cuisines=["Asian", "Malaysian", "Chinese", "Thai"],
        rating=4.3,
        approx_cost=550,
        votes=500,
    )
    criteria = FilterCriteria(
        location="Bangalore",
        budget="medium",
        cuisine="Chinese",
        min_rating=4.0,
    )
    result = apply_filters([multi, primary], criteria, bands, max_candidates=25)
    assert result.candidates[0].name == "Green Onion"


def test_filter_cuisine_italian(bands):
    criteria = FilterCriteria(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
    )
    result = apply_filters(_sample_restaurants(), criteria, bands, max_candidates=25)
    assert len(result.candidates) >= 1
    assert result.candidates[0].name == "Italian Place"


def test_filter_budget_low(bands):
    criteria = FilterCriteria(location="Bangalore", budget="low")
    result = apply_filters(_sample_restaurants(), criteria, bands, max_candidates=25)
    assert all(
        r.approx_cost is not None and r.approx_cost <= bands.low_max
        for r in result.candidates
    )


def test_filter_cap_max_candidates(bands):
    criteria = FilterCriteria(location="Bangalore", budget="medium")
    result = apply_filters(
        _sample_restaurants(),
        criteria,
        bands,
        max_candidates=2,
    )
    assert len(result.candidates) == 2
    assert result.total_matched == 3


def test_filter_empty_result(bands):
    criteria = FilterCriteria(
        location="Delhi",
        budget="medium",
        cuisine="Italian",
        min_rating=4.8,
    )
    result = apply_filters(_sample_restaurants(), criteria, bands)
    assert result.is_empty
    assert not result.should_call_llm
    assert result.message is not None
    assert len(result.suggestions) > 0


def test_filter_sorted_by_rating_then_votes(bands):
    criteria = FilterCriteria(location="Bangalore", budget="high")
    result = apply_filters(_sample_restaurants(), criteria, bands, max_candidates=25)
    if len(result.candidates) >= 2:
        assert result.candidates[0].rating >= result.candidates[1].rating


def test_validate_preferences_empty_location():
    with pytest.raises(ValueError, match="location"):
        validate_preferences(
            UserPreferences(location="  ", budget="medium"),
        )


def test_user_preferences_rejects_invalid_budget():
    with pytest.raises(ValidationError):
        UserPreferences(location="Bangalore", budget="invalid")  # type: ignore[arg-type]


def test_additional_preferences_not_used_in_filter(bands):
    """additional_preferences is LLM-only; must not change candidate set."""
    base = UserPreferences(location="Bangalore", budget="medium")
    with_extras = UserPreferences(
        location="Bangalore",
        budget="medium",
        additional_preferences="family-friendly rooftop vegan",
    )
    base_result = filter_preferences(_sample_restaurants(), base, bands)
    extras_result = filter_preferences(_sample_restaurants(), with_extras, bands)
    assert [r.id for r in base_result.candidates] == [r.id for r in extras_result.candidates]
    assert base_result.total_matched == extras_result.total_matched


def test_filter_optional_cuisine_and_rating(bands):
    criteria = FilterCriteria(location="Bangalore", budget="low")
    result = apply_filters(_sample_restaurants(), criteria, bands, max_candidates=25)
    assert not result.is_empty
    assert result.filters_applied["cuisine"] is None
    assert result.filters_applied["min_rating"] is None


def test_budget_edge_at_low_max_inclusive(bands):
    at_cap = Restaurant(
        id="edge",
        name="At Cap",
        location="Bangalore",
        cuisines=["Cafe"],
        rating=4.0,
        approx_cost=bands.low_max,
        votes=10,
    )
    over_cap = Restaurant(
        id="over",
        name="Over Cap",
        location="Bangalore",
        cuisines=["Cafe"],
        rating=4.0,
        approx_cost=bands.low_max + 1,
        votes=10,
    )
    criteria = FilterCriteria(location="Bangalore", budget="low")
    result = apply_filters([at_cap, over_cap], criteria, bands)
    assert len(result.candidates) == 1
    assert result.candidates[0].id == "edge"


def test_validate_preferences_unknown_location():
    with pytest.raises(ValueError, match="Location not found"):
        validate_preferences(
            UserPreferences(location="Atlantis", budget="medium"),
            available_locations=["Bangalore", "Delhi"],
        )


def test_filter_preferences_integration(bands):
    prefs = UserPreferences(
        location="Bangalore",
        budget="low",
        cuisine="Chinese",
        min_rating=3.5,
    )
    result = filter_preferences(
        _sample_restaurants(),
        prefs,
        bands,
        available_locations=["Bangalore", "Delhi", "BTM"],
    )
    assert not result.is_empty
    assert result.candidates[0].name == "Budget Chinese"


@pytest.mark.skipif(
    not __import__("src.config.settings", fromlist=["get_settings"])
    .get_settings()
    .data_cache_path.exists(),
    reason="Parquet cache required",
)
def test_repository_filter_bangalore_italian_medium():
    from src.data.repository import RestaurantRepository

    repo = RestaurantRepository()
    repo.load()
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = repo.filter(prefs)
    assert result.should_call_llm or result.is_empty
    if not result.is_empty:
        assert 1 <= len(result.candidates) <= 25
        assert all(
            r.location == "Bangalore" or "bangalore" in r.location.lower()
            for r in result.candidates
        )
        assert result.duration_ms is not None


@pytest.mark.skipif(
    not __import__("src.config.settings", fromlist=["get_settings"])
    .get_settings()
    .data_cache_path.exists(),
    reason="Parquet cache required",
)
def test_repository_filter_delhi_empty_on_bangalore_dataset():
    from src.data.repository import RestaurantRepository

    repo = RestaurantRepository()
    repo.load()
    prefs = UserPreferences(
        location="Delhi",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = repo.filter(prefs, validate_location=False)
    assert result.is_empty
    assert not result.should_call_llm
