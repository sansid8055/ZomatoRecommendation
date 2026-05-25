# Data Schema

> Processed cache: `data/processed/restaurants.parquet`  
> Default HF source: [shambhuraje/Swiggy_Vs_Zomato](https://huggingface.co/datasets/shambhuraje/Swiggy_Vs_Zomato)  
> Ingest filter: `DATA_METRO_FILTER=Hyderabad` → **~240 rows** in cache  
> Legacy source: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) (Bangalore-only)

## Swiggy_Vs_Zomato → Normalized Mapping (default)

| Raw column (HF) | Normalized field | Notes |
|-----------------|------------------|-------|
| `restaurant_id` | `id` | Stable ID from dataset |
| `restaurant_name` | `name` | Required |
| `city` | `location` | Metro city (e.g. **Hyderabad**); filtered on ingest |
| `locality` | `locality` | Neighborhood |
| `cuisines` | `cuisines` | Split on `,` |
| `zomato_rating` | `rating` | 0–5; fallback `average_rating_both_platforms` |
| `avg_cost_per_person_inr` | `approx_cost` | Integer INR (per-person proxy for budget bands) |
| `zomato_total_reviews` | `votes` | Review count |
| `restaurant_type` | `rest_type` | Optional |

## ManikaSaini (legacy) → Normalized Mapping

| Raw column (HF) | Normalized field | Notes |
|-----------------|------------------|-------|
| `name` | `name` | Required |
| `url` | `id` | Hash from `zomato.com/{city-slug}/...` |
| `address` | `location` | Metro from URL/address parse |
| `location` / `listed_in(city)` | `locality` | Area name |
| `rate` | `rating` | Parsed from `4.1/5` |
| `approx_cost(for two people)` | `approx_cost` | Cost for two (INR) |

## Processed Parquet Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Unique restaurant identifier |
| `name` | string | Restaurant name |
| `location` | string | Metro city (default cache: **Hyderabad**) |
| `locality` | string? | Area within city |
| `cuisines` | list[string] | Cuisine tags |
| `rating` | float? | 0–5 |
| `approx_cost` | int? | Cost proxy (INR) |
| `votes` | int? | Review count |
| `address` | string? | Full address |
| `rest_type` | string? | e.g. Casual Dining |
| `online_order` | string? | Yes/No |
| `book_table` | string? | Yes/No |

## Budget Bands

Stored at `data/processed/budget_bands.parquet`, computed from cost percentiles on the **Hyderabad** cache.

## City Aliases

See `CITY_ALIASES` and `URL_CITY_SLUG_ALIASES` in `src/data/ingestion.py` (e.g. Bengaluru → Bangalore, hyderabad → Hyderabad).

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_DATASET_ID` | `shambhuraje/Swiggy_Vs_Zomato` | Hugging Face dataset |
| `DATA_METRO_FILTER` | `Hyderabad` | Rows kept at ingest |
| `DEFAULT_METRO_CITY` | `Hyderabad` | UI default location |

Rebuild cache: `python scripts/download_dataset.py --force`
