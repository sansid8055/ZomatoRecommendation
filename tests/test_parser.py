import json

import pytest

from src.data.models import Restaurant, UserPreferences
from src.config.settings import get_settings
from src.llm.client import ConfigurationError, MockLLMClient, get_llm_client
from src.llm.engine import RecommendationEngine
from src.llm.parser import (
    build_fallback_output,
    extract_json_text,
    parse_llm_response,
)


def _candidates(n: int = 10) -> list[Restaurant]:
    return [
        Restaurant(
            id=str(i),
            name=f"Restaurant {i}",
            location="Bangalore",
            cuisines=[["Italian", "Chinese"][i % 2]],
            rating=4.0 + (i % 5) * 0.1,
            approx_cost=400 + i * 50,
            votes=100 + i,
        )
        for i in range(1, n + 1)
    ]


def test_extract_json_from_markdown_fence():
    raw = '```json\n{"summary": "Hi", "recommendations": []}\n```'
    assert "recommendations" in extract_json_text(raw)


def test_parse_valid_json():
    valid_ids = {"1", "2", "3"}
    raw = json.dumps(
        {
            "summary": "Great Italian picks.",
            "recommendations": [
                {"restaurant_id": "1", "rank": 1, "explanation": "Best Italian."},
                {"restaurant_id": "2", "rank": 2, "explanation": "Good Chinese."},
            ],
        }
    )
    result = parse_llm_response(raw, valid_ids, top_k=5)
    assert result.summary == "Great Italian picks."
    assert len(result.recommendations) == 2
    assert result.recommendations[0].restaurant_id == "1"
    assert result.recommendations[0].rank == 1


def test_parse_strips_hallucinated_ids():
    valid_ids = {"1"}
    raw = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "1", "rank": 1, "explanation": "Valid."},
                {"restaurant_id": "999", "rank": 2, "explanation": "Fake."},
            ]
        }
    )
    result = parse_llm_response(raw, valid_ids, top_k=5)
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant_id == "1"


def test_parse_duplicate_ids_deduped():
    valid_ids = {"1", "2"}
    raw = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "1", "rank": 1, "explanation": "A"},
                {"restaurant_id": "1", "rank": 2, "explanation": "Dup"},
            ]
        }
    )
    result = parse_llm_response(raw, valid_ids, top_k=5)
    assert len(result.recommendations) == 1


def test_parse_caps_top_k():
    valid_ids = {str(i) for i in range(1, 11)}
    items = [
        {"restaurant_id": str(i), "rank": i, "explanation": f"R{i}"}
        for i in range(1, 11)
    ]
    raw = json.dumps({"recommendations": items})
    result = parse_llm_response(raw, valid_ids, top_k=5)
    assert len(result.recommendations) == 5


def test_parse_malformed_raises():
    with pytest.raises((ValueError, json.JSONDecodeError)):
        parse_llm_response("not json at all", {"1"}, top_k=5)


def test_fallback_output():
    candidates = _candidates(5)
    prefs = UserPreferences(location="Bangalore", budget="medium", cuisine="Italian")
    result = build_fallback_output(candidates, prefs, top_k=3)
    assert result.degraded_mode is True
    assert len(result.recommendations) == 3
    assert all(r.restaurant_id in {c.id for c in candidates} for r in result.recommendations)


def test_engine_with_mock_client():
    candidates = _candidates(10)
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    mock = MockLLMClient(candidates, top_k=5)
    engine = RecommendationEngine(client=mock)
    result = engine.rank_and_explain(candidates, prefs, top_k=5)

    assert not result.degraded_mode
    assert len(result.recommendations) == 5
    valid = {c.id for c in candidates}
    assert all(r.restaurant_id in valid for r in result.recommendations)
    assert result.recommendations[0].rank == 1


def test_get_llm_client_requires_groq_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "")
    get_settings.cache_clear()
    try:
        with pytest.raises(ConfigurationError, match="GROQ_API_KEY"):
            get_llm_client()
    finally:
        get_settings.cache_clear()


def test_engine_retry_then_fallback_on_bad_json():
    candidates = _candidates(5)
    prefs = UserPreferences(location="Bangalore", budget="medium")
    mock = MockLLMClient(candidates, top_k=3)
    mock.set_next_response("broken response")
    mock.set_next_response("still not json")

    engine = RecommendationEngine(client=mock)
    result = engine.rank_and_explain(candidates, prefs, top_k=3)

    assert result.degraded_mode is True
    assert len(result.recommendations) == 3
