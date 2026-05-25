import pytest

from src.config.settings import get_settings
from src.data.models import Restaurant, UserPreferences
from src.data.repository import RestaurantRepository
from src.domain.budget import BudgetBands
from src.domain.filters import apply_filters, FilterCriteria
from src.llm.client import MockLLMClient
from src.services.orchestrator import (
    RecommendationOrchestrator,
    _enrich_recommendations,
    get_recommendations,
)
from src.llm.models import LLMRecommendationItem, LLMRecommendationOutput


def _sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="1",
            name="Italian Place",
            location="Bangalore",
            cuisines=["Italian"],
            rating=4.5,
            approx_cost=600,
            votes=500,
        ),
        Restaurant(
            id="2",
            name="Budget Chinese",
            location="Bangalore",
            cuisines=["Chinese"],
            rating=3.8,
            approx_cost=250,
            votes=200,
        ),
        Restaurant(
            id="3",
            name="Fine Dining",
            location="Bangalore",
            cuisines=["North Indian"],
            rating=4.9,
            approx_cost=1200,
            votes=800,
        ),
    ]


class InMemoryRepository:
    """Lightweight repository stub for orchestrator tests."""

    def __init__(self, restaurants: list[Restaurant], bands: BudgetBands) -> None:
        self._restaurants = restaurants
        self._bands = bands
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        self._loaded = True

    def get_all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_available_locations(self) -> list[str]:
        return ["Bangalore"]

    def get_budget_bands(self) -> BudgetBands:
        return self._bands

    def get_by_ids(self, ids: list[str]) -> list[Restaurant]:
        id_set = set(ids)
        return [r for r in self._restaurants if r.id in id_set]

    def filter(self, prefs: UserPreferences, *, validate_location: bool = True):
        criteria = FilterCriteria.from_preferences(prefs)
        return apply_filters(self._restaurants, criteria, self._bands)


@pytest.fixture
def bands() -> BudgetBands:
    return BudgetBands(low_max=500, medium_min=501, medium_max=1500, high_min=1501)


@pytest.fixture
def stub_repo(bands) -> InMemoryRepository:
    return InMemoryRepository(_sample_restaurants(), bands)


def test_enrich_dedupes_duplicate_chain_names(stub_repo):
    llm_output = LLMRecommendationOutput(
        recommendations=[
            LLMRecommendationItem(restaurant_id="1", rank=1, explanation="A"),
            LLMRecommendationItem(restaurant_id="1", rank=2, explanation="Dup id"),
        ]
    )
    enriched = _enrich_recommendations(llm_output, stub_repo, top_k=5)
    assert len(enriched) == 1


def test_enrich_skips_unknown_ids(stub_repo):
    llm_output = LLMRecommendationOutput(
        recommendations=[
            LLMRecommendationItem(restaurant_id="1", rank=1, explanation="Good."),
            LLMRecommendationItem(restaurant_id="999", rank=2, explanation="Fake."),
        ]
    )
    enriched = _enrich_recommendations(llm_output, stub_repo)
    assert len(enriched) == 1
    assert enriched[0].name == "Italian Place"


def test_orchestrator_empty_filter_short_circuits_llm(stub_repo):
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Martian",
        min_rating=5.0,
    )
    mock = MockLLMClient(_sample_restaurants())
    orchestrator = RecommendationOrchestrator(
        repository=stub_repo,
        llm_client=mock,
    )
    response = orchestrator.get_recommendations(prefs, validate_location=False)

    assert response.success is True
    assert response.recommendations == []
    assert response.metadata.candidate_count == 0
    assert response.message is not None
    assert len(response.suggestions) > 0


def test_orchestrator_full_pipeline_with_mock(stub_repo):
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    mock = MockLLMClient(
        [r for r in _sample_restaurants() if r.rating and r.rating >= 4.0],
        top_k=2,
    )
    orchestrator = RecommendationOrchestrator(
        repository=stub_repo,
        llm_client=mock,
    )
    response = orchestrator.get_recommendations(prefs, validate_location=False)

    assert response.success is True
    assert response.metadata.candidate_count > 0
    assert len(response.recommendations) >= 1
    rec = response.recommendations[0]
    assert rec.name
    assert rec.cuisine
    assert rec.explanation
    assert rec.rank >= 1
    assert rec.restaurant_id in {"1", "3"}


def test_orchestrator_missing_api_key_fail_fast(stub_repo, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    get_settings.cache_clear()

    prefs = UserPreferences(location="Bangalore", budget="medium")
    orchestrator = RecommendationOrchestrator(repository=stub_repo)
    response = orchestrator.get_recommendations(
        prefs,
        fail_without_api_key=True,
        validate_location=False,
    )

    assert response.success is False
    assert response.recommendations == []
    assert "API key" in (response.message or "").lower() or "GROQ" in (response.message or "")
    get_settings.cache_clear()


@pytest.mark.skipif(
    not get_settings().data_cache_path.exists(),
    reason="Parquet cache required",
)
def test_get_recommendations_cli_exit_criteria():
    """Bangalore + Chinese + medium + min_rating 4.0 → enriched results."""
    get_settings.cache_clear()
    repo = RestaurantRepository()
    repo.load()

    filtered = repo.filter(
        UserPreferences(
            location="Bangalore",
            budget="medium",
            cuisine="Chinese",
            min_rating=4.0,
        )
    )
    mock = MockLLMClient(filtered.candidates[:10], top_k=5)

    response = get_recommendations(
        UserPreferences(
            location="Bangalore",
            budget="medium",
            cuisine="Chinese",
            min_rating=4.0,
        ),
        repository=repo,
        llm_client=mock,
        validate_location=False,
    )

    assert response.success is True
    assert response.metadata.candidate_count > 0
    assert len(response.recommendations) >= 1
    for rec in response.recommendations:
        assert rec.name
        assert rec.cuisine
        assert rec.explanation
        assert rec.location
