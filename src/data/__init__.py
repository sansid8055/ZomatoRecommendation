from src.data.models import BudgetTier, Restaurant, UserPreferences

__all__ = [
    "BudgetTier",
    "Restaurant",
    "UserPreferences",
    "RestaurantRepository",
]


def __getattr__(name: str):
    """Lazy import avoids circular dependency with src.domain.budget."""
    if name == "RestaurantRepository":
        from src.data.repository import RestaurantRepository

        return RestaurantRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
