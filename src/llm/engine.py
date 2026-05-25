"""LLM recommendation engine: prompt → complete → parse → validate → fallback."""

from __future__ import annotations

import json
import logging
import time

from src.config.settings import get_settings
from src.data.models import Restaurant, UserPreferences
from src.llm.client import ConfigurationError, RecommendationLLM, get_llm_client
from src.llm.models import LLMRecommendationOutput
from src.llm.parser import build_fallback_output, parse_llm_response
from src.llm.prompts import build_prompts, build_retry_user_prompt

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(self, client: RecommendationLLM | None = None) -> None:
        self._client = client

    def _get_client(self) -> RecommendationLLM:
        if self._client is not None:
            return self._client
        return get_llm_client()

    def rank_and_explain(
        self,
        candidates: list[Restaurant],
        prefs: UserPreferences,
        *,
        top_k: int | None = None,
    ) -> LLMRecommendationOutput:
        """
        Rank candidates with LLM; validate IDs; fallback on failure.
        """
        if not candidates:
            return LLMRecommendationOutput(
                summary=None,
                recommendations=[],
                degraded_mode=False,
            )

        settings = get_settings()
        k = top_k if top_k is not None else settings.top_k_results
        valid_ids = {str(r.id) for r in candidates}

        system_prompt, user_prompt = build_prompts(candidates, prefs, top_k=k)

        try:
            client = self._get_client()
        except ConfigurationError:
            logger.warning("LLM not configured; using fallback ranking")
            return build_fallback_output(candidates, prefs, top_k=k)

        start = time.perf_counter()
        result = self._complete_with_retry(
            client,
            system_prompt,
            user_prompt,
            valid_ids,
            k,
            candidates,
            prefs,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info("LLM ranking completed in %.1f ms", latency_ms)

        return result

    def _complete_with_retry(
        self,
        client: RecommendationLLM,
        system_prompt: str,
        user_prompt: str,
        valid_ids: set[str],
        top_k: int,
        candidates: list[Restaurant],
        prefs: UserPreferences,
    ) -> LLMRecommendationOutput:
        last_error: Exception | None = None

        for attempt in range(2):
            try:
                prompt = user_prompt if attempt == 0 else build_retry_user_prompt(user_prompt)
                response_text = client.complete(system_prompt, prompt)
                return parse_llm_response(response_text, valid_ids, top_k=top_k)
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.warning("LLM parse failed (attempt %s): %s", attempt + 1, exc)
            except Exception as exc:
                last_error = exc
                logger.warning("LLM call failed (attempt %s): %s", attempt + 1, exc)
                break

        logger.warning("Using degraded fallback ranking: %s", last_error)
        return build_fallback_output(candidates, prefs, top_k=top_k)
