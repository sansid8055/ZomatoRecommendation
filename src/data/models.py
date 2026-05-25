from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BudgetTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Restaurant(BaseModel):
    """Normalized restaurant row for filtering and LLM prompts."""

    id: str
    name: str
    location: str  # city (listed_in(city)), used for user location filter
    locality: str | None = None
    cuisines: list[str] = Field(default_factory=list)
    rating: float | None = None
    approx_cost: int | None = None
    votes: int | None = None
    address: str | None = None
    rest_type: str | None = None
    online_order: str | None = None
    book_table: str | None = None

    model_config = {"frozen": True}


class UserPreferences(BaseModel):
    """Collected from UI; full validation expanded in Phase 2."""

    location: str
    budget: Literal["low", "medium", "high"]
    cuisine: str | None = None
    min_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    additional_preferences: str | None = None

    @field_validator("location", "cuisine", "additional_preferences", mode="before")
    @classmethod
    def _strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("cuisine")
    @classmethod
    def _cap_cuisine_length(cls, value: str | None) -> str | None:
        if value and len(value) > 100:
            return value[:100]
        return value

    @field_validator("additional_preferences")
    @classmethod
    def _cap_additional_length(cls, value: str | None) -> str | None:
        if value and len(value) > 500:
            return value[:500]
        return value
