"""In-memory restaurant store backed by processed Parquet."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config.settings import get_settings
from src.data.ingestion import (
    dataframe_to_restaurants,
    load_budget_bands,
    run_ingestion,
)
from src.data.models import Restaurant, UserPreferences
from src.domain.budget import BudgetBands, compute_budget_bands
from src.domain.filters import FilterCriteria, FilterResult, apply_filters, validate_preferences


class RestaurantRepository:
    def __init__(self, cache_path: Path | None = None) -> None:
        settings = get_settings()
        self._cache_path = cache_path or settings.data_cache_path
        self._bands_path = self._cache_path.parent / "budget_bands.parquet"
        self._df: pd.DataFrame | None = None
        self._restaurants: list[Restaurant] | None = None
        self._budget_bands: BudgetBands | None = None

    @property
    def is_loaded(self) -> bool:
        return self._df is not None

    def load(self, *, force_refresh: bool = False) -> None:
        settings = get_settings()
        df, bands = run_ingestion(
            settings.hf_dataset_id,
            self._cache_path,
            force=force_refresh,
        )
        self._df = df
        self._budget_bands = bands
        self._restaurants = dataframe_to_restaurants(df)

    def _ensure_loaded(self) -> pd.DataFrame:
        if self._df is None:
            self.load()
        assert self._df is not None
        return self._df

    def get_all(self) -> list[Restaurant]:
        self._ensure_loaded()
        assert self._restaurants is not None
        return list(self._restaurants)

    def get_dataframe(self) -> pd.DataFrame:
        return self._ensure_loaded().copy()

    def get_budget_bands(self) -> BudgetBands:
        self._ensure_loaded()
        if self._budget_bands is None:
            self._budget_bands = load_budget_bands(self._bands_path)
        if self._budget_bands is None:
            self._budget_bands = compute_budget_bands(self._df["approx_cost"])
        return self._budget_bands

    def get_by_ids(self, ids: list[str]) -> list[Restaurant]:
        if not ids:
            return []
        id_set = {str(i) for i in ids}
        return [r for r in self.get_all() if r.id in id_set]

    def get_available_locations(self) -> list[str]:
        """Metro cities and areas for UI dropdown (metros first)."""
        df = self._ensure_loaded()
        locations = sorted(df["location"].dropna().unique().tolist())
        metro_order = (
            "Bangalore",
            "Hyderabad",
            "Delhi",
            "Mumbai",
            "Chennai",
            "Kolkata",
            "Pune",
        )
        metros = [loc for loc in metro_order if loc in locations]
        metros += [loc for loc in locations if loc not in metros]
        
        # Add all unique localities/areas in the dataset (excluding metro names)
        localities = []
        if "locality" in df.columns:
            raw_localities = sorted(df["locality"].dropna().unique().tolist())
            metro_lower = {m.lower() for m in metros}
            localities = [
                loc for loc in raw_localities
                if loc and loc.strip() and loc.lower() not in metro_lower
            ]
        
        return metros + localities

    def filter_by_location(self, location: str) -> list[Restaurant]:
        """Match metro city or area/locality (Phase 1 helper; used by tests)."""
        if not location or not location.strip():
            return []
        needle = location.strip().lower()
        return [
            r
            for r in self.get_all()
            if r.location.lower() == needle
            or needle in r.location.lower()
            or (
                r.locality is not None
                and (
                    r.locality.lower() == needle
                    or needle in r.locality.lower()
                )
            )
        ]

    def filter(
        self,
        prefs: UserPreferences,
        *,
        criteria: FilterCriteria | None = None,
        validate_location: bool = True,
    ) -> FilterResult:
        """
        Full filter pipeline: location → rating → cuisine → budget → sort & cap.
        Returns empty result with suggestions when no matches (no LLM call).
        """
        if validate_location:
            validate_preferences(prefs, self.get_available_locations())

        filter_criteria = criteria or FilterCriteria.from_preferences(prefs)
        bands = self.get_budget_bands()
        return apply_filters(
            self.get_all(),
            filter_criteria,
            bands,
        )

    def count(self) -> int:
        return len(self._ensure_loaded())
