from src.domain.budget import BudgetBands, compute_budget_bands, cost_in_budget

__all__ = [
    "BudgetBands",
    "compute_budget_bands",
    "cost_in_budget",
    "FilterCriteria",
    "FilterResult",
    "apply_filters",
    "filter_preferences",
    "validate_preferences",
]

_FILTER_EXPORTS = {
    "FilterCriteria",
    "FilterResult",
    "apply_filters",
    "filter_preferences",
    "validate_preferences",
}


def __getattr__(name: str):
    if name in _FILTER_EXPORTS:
        from src.domain import filters as _filters

        return getattr(_filters, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
