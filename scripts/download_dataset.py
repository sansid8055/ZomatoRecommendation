#!/usr/bin/env python3
"""Download Zomato dataset from Hugging Face and write processed Parquet cache."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import get_settings
from src.data.ingestion import run_ingestion


def main() -> int:
    parser = argparse.ArgumentParser(description="Build restaurant Parquet cache")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and rebuild cache even if Parquet exists",
    )
    args = parser.parse_args()

    settings = get_settings()
    cache_path = settings.data_cache_path

    print(f"Dataset:      {settings.hf_dataset_id}")
    print(f"Metro filter: {settings.data_metro_filter or '(all cities)'}")
    print(f"Cache:        {cache_path}")

    df, bands = run_ingestion(
        settings.hf_dataset_id,
        cache_path,
        force=args.force,
        metro_filter=settings.data_metro_filter,
    )

    print(f"Rows written: {len(df):,}")
    print(f"Budget bands: {bands.describe()}")
    print(f"Metro cities: {df['location'].nunique()} -> {sorted(df['location'].unique().tolist())}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
