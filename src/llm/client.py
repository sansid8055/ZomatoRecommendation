"""LLM client adapters for restaurant ranking (Phase 3 — Groq MVP)."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when LLM is not configured (e.g. missing API key)."""


class RecommendationLLM(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return raw model text (expected JSON)."""


class GroqRecommendationLLM(RecommendationLLM):
    """Groq chat-completions adapter with retry/backoff for rate limits."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.groq_api_key
        self._model = model or settings.llm_model
        self._temperature = (
            settings.llm_temperature if temperature is None else temperature
        )
        self._max_tokens = settings.llm_max_tokens if max_tokens is None else max_tokens
        self._timeout = settings.llm_timeout if timeout is None else timeout
        self._max_retries = max_retries

        if not self._api_key or not str(self._api_key).strip():
            raise ConfigurationError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key "
                "from https://console.groq.com/keys"
            )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        from groq import APIConnectionError, APIStatusError, Groq, RateLimitError

        client = Groq(api_key=self._api_key, timeout=self._timeout)
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("Empty response from LLM")
                return content.strip()
            except RateLimitError as exc:
                last_error = exc
                wait = min(2**attempt, 30)
                logger.warning("Groq rate limit; retry in %ss (attempt %s)", wait, attempt)
                time.sleep(wait)
            except (APIConnectionError, APIStatusError) as exc:
                last_error = exc
                status = getattr(exc, "status_code", None)
                if status == 401:
                    raise ConfigurationError(
                        "Invalid GROQ_API_KEY. Check your .env configuration."
                    ) from exc
                if attempt < self._max_retries:
                    wait = min(2**attempt, 15)
                    logger.warning("Groq API error %s; retry in %ss", exc, wait)
                    time.sleep(wait)
                else:
                    raise
            except Exception as exc:
                last_error = exc
                raise

        raise RuntimeError(f"Groq request failed after retries: {last_error}")


class MockLLMClient(RecommendationLLM):
    """Deterministic client for tests; ranks candidates by input order."""

    def __init__(
        self,
        candidates: list | None = None,
        *,
        summary: str | None = None,
        top_k: int = 5,
    ) -> None:
        self._candidates = candidates or []
        self._summary = summary or "Mock summary for test recommendations."
        self._top_k = top_k
        self._response_queue: list[str] = []

    def set_next_response(self, raw_text: str) -> None:
        """Queue a response for the next complete() call (FIFO)."""
        self._response_queue.append(raw_text)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if self._response_queue:
            return self._response_queue.pop(0)
        items = []
        for i, c in enumerate(self._candidates[: self._top_k], start=1):
            rid = str(getattr(c, "id", c.get("id") if isinstance(c, dict) else i))
            name = getattr(c, "name", None) or (
                c.get("name") if isinstance(c, dict) else "Restaurant"
            )
            items.append(
                {
                    "restaurant_id": rid,
                    "rank": i,
                    "explanation": f"{name} is a strong match for your preferences.",
                }
            )
        payload = {"summary": self._summary, "recommendations": items}
        return json.dumps(payload)


def get_llm_client(*, use_mock: bool = False) -> RecommendationLLM:
    if use_mock:
        return MockLLMClient()
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider == "groq":
        return GroqRecommendationLLM()
    raise ConfigurationError(
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Supported: groq"
    )
