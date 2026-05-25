"""Budget tier thresholds derived from dataset cost distribution."""

from dataclasses import dataclass

import pandas as pd

from src.data.models import BudgetTier


@dataclass(frozen=True)
class BudgetBands:
    """Cost-for-two (INR) bands: low < p33, medium p33–p66, high > p66."""

    low_max: int
    medium_min: int
    medium_max: int
    high_min: int

    def describe(self) -> str:
        return (
            f"low: <= {self.low_max}, "
            f"medium: {self.medium_min}-{self.medium_max}, "
            f"high: >= {self.high_min}"
        )


def compute_budget_bands(costs: pd.Series) -> BudgetBands:
    """Compute percentile-based bands from non-null positive costs."""
    valid = costs.dropna()
    valid = valid[valid > 0]
    if valid.empty:
        return BudgetBands(low_max=500, medium_min=501, medium_max=1500, high_min=1501)

    p33 = int(valid.quantile(0.33))
    p66 = int(valid.quantile(0.66))
    p33 = max(p33, 1)
    p66 = max(p66, p33 + 1)

    return BudgetBands(
        low_max=p33,
        medium_min=p33 + 1,
        medium_max=p66,
        high_min=p66 + 1,
    )


def cost_in_budget(cost: int | None, tier: BudgetTier | str, bands: BudgetBands) -> bool:
    """Return True if cost fits the budget tier; null cost excluded from budget filter."""
    if cost is None:
        return False

    tier_value = tier.value if isinstance(tier, BudgetTier) else str(tier).lower()

    if tier_value == BudgetTier.LOW.value:
        return cost <= bands.low_max
    if tier_value == BudgetTier.MEDIUM.value:
        return bands.medium_min <= cost <= bands.medium_max
    if tier_value == BudgetTier.HIGH.value:
        return cost >= bands.high_min
    return False
