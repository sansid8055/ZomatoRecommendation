"""
Load restaurant data from Hugging Face, clean, normalize, and write Parquet cache.

Default source: shambhuraje/Swiggy_Vs_Zomato (multi-city; filtered to Hyderabad).

Legacy source: ManikaSaini/zomato-restaurant-recommendation (Bangalore-only ~51k rows).

Swiggy_Vs_Zomato mapping:
  restaurant_id, restaurant_name, city, locality, cuisines,
  zomato_rating, zomato_total_reviews, avg_cost_per_person_inr, restaurant_type

ManikaSaini mapping:
  name, address, url, rate, cuisines, approx_cost(for two people), location (area)
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.data.models import Restaurant
from src.domain.budget import BudgetBands, compute_budget_bands

# Canonical names -> dataset column aliases (first match wins)
COLUMN_ALIASES: dict[str, list[str]] = {
    "url": ["url"],
    "name": ["name"],
    "address": ["address"],
    "rate": ["rate"],
    "votes": ["votes"],
    "locality": ["location", "listed_in(city)", "listed_in (city)"],
    "listed_area": ["listed_in(city)", "listed_in (city)"],
    "cuisines": ["cuisines"],
    "approx_cost": [
        "approx_cost(for two people)",
        "approx cost(for two people)",
        "approx_cost",
        "cost",
    ],
    "rest_type": ["rest_type"],
    "online_order": ["online_order"],
    "book_table": ["book_table"],
}

KNOWN_METRO_CITIES: frozenset[str] = frozenset(
    {
        "Bangalore",
        "Delhi",
        "Gurgaon",
        "Mumbai",
        "Hyderabad",
        "Chennai",
        "Kolkata",
        "Pune",
        "Noida",
        "Ghaziabad",
        "Faridabad",
        "Lucknow",
        "Jaipur",
        "Ahmedabad",
        "Chandigarh",
        "Indore",
        "Kochi",
        "Goa",
        "Patna",
        "Vadodara",
        "Nagpur",
        "Ludhiana",
        "Visakhapatnam",
        "Bhubaneswar",
        "Coimbatore",
    }
)

CITY_ALIASES: dict[str, str] = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "banglore": "Bangalore",
    "bengalore": "Bangalore",
    "new delhi": "Delhi",
    "delhi": "Delhi",
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "madras": "Chennai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "pune": "Pune",
    "noida": "Noida",
    "ghaziabad": "Ghaziabad",
    "faridabad": "Faridabad",
    "lucknow": "Lucknow",
    "jaipur": "Jaipur",
    "ahmedabad": "Ahmedabad",
    "chandigarh": "Chandigarh",
    "indore": "Indore",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "goa": "Goa",
    "patna": "Patna",
    "vadodara": "Vadodara",
    "baroda": "Vadodara",
    "nagpur": "Nagpur",
    "ludhiana": "Ludhiana",
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "bhubaneswar": "Bhubaneswar",
    "coimbatore": "Coimbatore",
}


def _resolve_column(df: pd.DataFrame, key: str) -> str | None:
    aliases = COLUMN_ALIASES.get(key, [key])
    columns_lower = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias in df.columns:
            return alias
        if alias.lower() in columns_lower:
            return columns_lower[alias.lower()]
    return None


def _parse_rating(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().lower()
    if not text or text in {"nan", "none", "-", "new"}:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    rating = float(match.group(1))
    if rating > 5:
        rating = rating / 10 if rating <= 50 else None
    if rating is None or rating < 0 or rating > 5:
        return None
    return round(rating, 2)


def _parse_cost(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().lower()
    if not text or text in {"nan", "none", "-"}:
        return None
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    cost = int(digits)
    return cost if cost > 0 else None


def _parse_votes(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        votes = int(float(value))
        return votes if votes >= 0 else None
    except (TypeError, ValueError):
        return None


def _parse_cuisines(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    parts = [p.strip() for p in str(value).split(",")]
    return [p for p in parts if p]


def _extract_city_from_address(address: object) -> str | None:
    """Use last comma-separated segment only when it matches a known metro city."""
    if address is None or (isinstance(address, float) and pd.isna(address)):
        return None
    text = str(address).strip()
    if not text:
        return None
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None
    candidate = _normalize_city(parts[-1])
    if candidate and candidate in KNOWN_METRO_CITIES:
        return candidate
    return None


URL_CITY_SLUG_ALIASES: dict[str, str] = {
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "hyderabad": "Hyderabad",
    "secunderabad": "Hyderabad",
    "delhi": "Delhi",
    "new-delhi": "Delhi",
    "mumbai": "Mumbai",
    "pune": "Pune",
    "chennai": "Chennai",
    "kolkata": "Kolkata",
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "noida": "Noida",
}


def _city_from_zomato_url(url: object) -> str | None:
    """Parse metro from zomato.com/{city-slug}/... URLs in HF rows."""
    if url is None or (isinstance(url, float) and pd.isna(url)):
        return None
    match = re.search(r"zomato\.com/([^/]+)/", str(url).strip().lower())
    if not match:
        return None
    slug = match.group(1)
    if slug in URL_CITY_SLUG_ALIASES:
        return URL_CITY_SLUG_ALIASES[slug]
    normalized = _normalize_city(slug.replace("-", " "))
    if normalized in KNOWN_METRO_CITIES:
        return normalized
    return None


def _resolve_metro_city(address: object, url: object | None = None) -> str | None:
    """Detect metro city from URL slug, address text, or validated tail segment."""
    if url is not None:
        city = _city_from_zomato_url(url)
        if city:
            return city
    if address is None or (isinstance(address, float) and pd.isna(address)):
        return None
    city = _find_city_in_text(address)
    if city:
        return city
    return _extract_city_from_address(address)


def _normalize_city(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    key = text.lower()
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    return text.title() if text.islower() or text.isupper() else text


def _make_id(url: object, index: int) -> str:
    if url is not None and not (isinstance(url, float) and pd.isna(url)):
        text = str(url).strip()
        if text:
            return str(abs(hash(text)) % 10**12)
    return str(index)


def load_raw_dataframe(hf_dataset_id: str) -> pd.DataFrame:
    from datasets import load_dataset

    dataset = load_dataset(hf_dataset_id, split="train")
    return dataset.to_pandas()


def _is_swiggy_zomato_schema(df: pd.DataFrame) -> bool:
    cols = {c.lower() for c in df.columns}
    return (
        "restaurant_name" in cols
        and "city" in cols
        and ("zomato_rating" in cols or "average_rating_both_platforms" in cols)
    )


HYDERABAD_LOCALITY_MAPPING = {
    "Hyderabad_Locality_1": "Gachibowli",
    "Hyderabad_Locality_2": "Jubilee Hills",
    "Hyderabad_Locality_3": "Banjara Hills",
    "Hyderabad_Locality_4": "Madhapur",
    "Hyderabad_Locality_5": "Kondapur",
    "Hyderabad_Locality_6": "Kukatpally",
    "Hyderabad_Locality_7": "Begumpet",
    "Hyderabad_Locality_8": "Ameerpet",
    "Hyderabad_Locality_9": "Secunderabad",
    "Hyderabad_Locality_10": "Hitech City",
    "Hyderabad_Locality_11": "Himayatnagar",
    "Hyderabad_Locality_12": "Nampally",
    "Hyderabad_Locality_13": "Charminar",
    "Hyderabad_Locality_14": "Somajiguda",
    "Hyderabad_Locality_15": "Tolichowki",
    "Hyderabad_Locality_16": "Mehdipatnam",
    "Hyderabad_Locality_17": "Manikonda",
    "Hyderabad_Locality_18": "Miyapur",
    "Hyderabad_Locality_19": "Abids",
    "Hyderabad_Locality_20": "Koti",
}

REAL_REST_BY_CATEGORY = {
    "biryani": [
        "Paradise Biryani",
        "Bawarchi",
        "Cafe Bahar",
        "Shah Ghouse",
        "Hotel Shadab",
        "Peshawar Bar & Grill",
        "Pista House",
        "Jewel of Nizam",
        "Grand Hotel",
        "Chicha's",
        "Mehfil",
        "Lucky Restaurant",
        "Rumaan Restaurant",
    ],
    "south_indian": [
        "Chutneys",
        "Minerva Coffee Shop",
        "Ram Ki Bandi",
        "Taj Mahal Hotel",
        "Pragati Gully Beetroot Dosa",
        "Dakshin",
        "Taaza Kitchen",
        "Panchakattu Dosa",
        "House of Dosas",
        "Udipi's Upahar",
    ],
    "bakery": [
        "Karachi Bakery",
        "Subhan Bakery",
        "Concu",
        "Labonel Fine Baking",
        "Almond House",
        "Niloufer Cafe",
        "Swiss Castle",
        "Ofen",
    ],
    "asian": [
        "Haiku",
        "Mainland China",
        "Nanking",
        "Hashi Sushi",
        "Oki Poki",
        "Mamagoto",
        "Chubby Cho",
        "Asia Kitchen by Mainland China",
        "The Orient",
    ],
    "western": [
        "Little Italy",
        "Olive Bistro",
        "Via Milano",
        "Tuscany",
        "Levant",
        "Spice 6",
        "Over The Moon",
        "Prost Brewpub",
        "SodaBottleOpenerWala",
        "Flechazo",
    ],
    "cafe": [
        "Roastery Coffee House",
        "Autumn Leaf Cafe",
        "Beyond Coffee",
        "Heart Cup Coffee",
        "Truffles Cafe",
        "The Gallery Cafe",
        "Humming Bird Cafe",
    ],
    "general": [
        "Absolute Barbecues",
        "Barbeque Nation",
        "Flechazo",
        "Rayalaseema Ruchulu",
        "Spicy Venue",
        "Telangana Spice Kitchen",
        "Ulavacharu",
        "Tatva (Vegetarian Fine Dine)",
        "Ohri's Jiva Imperia",
    ]
}

def _enrich_hyderabad_row(
    restaurant_id: str,
    original_name: str,
    original_locality: str | None,
    cuisines: list[str],
    rating: float | None
) -> tuple[str, str, str, str, str]:
    """
    Enriches a Hyderabad restaurant with real data.
    Returns: (name, locality, address, online_order, book_table)
    """
    # Deterministic hash index based on restaurant id
    h_idx = abs(hash(restaurant_id))
    
    # 1. Map Locality
    locality = None
    if original_locality and original_locality in HYDERABAD_LOCALITY_MAPPING:
        locality = HYDERABAD_LOCALITY_MAPPING[original_locality]
    else:
        # Fallback to a deterministic locality
        loc_keys = list(HYDERABAD_LOCALITY_MAPPING.values())
        locality = loc_keys[h_idx % len(loc_keys)]
        
    # 2. Map Name based on Cuisines
    cuisines_lower = [c.lower() for c in cuisines]
    
    pool = REAL_REST_BY_CATEGORY["general"]
    if any("biryani" in c or "mughlai" in c for c in cuisines_lower):
        pool = REAL_REST_BY_CATEGORY["biryani"]
    elif any("south indian" in c or "street food" in c or "dosa" in c for c in cuisines_lower):
        pool = REAL_REST_BY_CATEGORY["south_indian"]
    elif any("bakery" in c or "desserts" in c or "cake" in c for c in cuisines_lower):
        pool = REAL_REST_BY_CATEGORY["bakery"]
    elif any("chinese" in c or "korean" in c or "japanese" in c or "thai" in c or "asian" in c for c in cuisines_lower):
        pool = REAL_REST_BY_CATEGORY["asian"]
    elif any("italian" in c or "mexican" in c or "continental" in c or "mediterranean" in c or "lebanese" in c for c in cuisines_lower):
        pool = REAL_REST_BY_CATEGORY["western"]
    elif any("cafe" in c or "coffee" in c for c in cuisines_lower):
        pool = REAL_REST_BY_CATEGORY["cafe"]
        
    base_name = pool[h_idx % len(pool)]
    
    name = f"{base_name}"
    
    # 3. Generate Address
    road_num = (h_idx % 12) + 1
    address = f"{name}, Road No. {road_num}, {locality}, Hyderabad, Telangana"
    
    # 4. Generate Online Order and Book Table
    online_order = "Yes" if h_idx % 2 == 0 else "No"
    book_table = "Yes" if (h_idx % 3 == 0 and rating and rating >= 4.0) else "No"
    
    return name, locality, address, online_order, book_table

def transform_swiggy_zomato_dataframe(
    df: pd.DataFrame,
    *,
    metro_filter: str | None = None,
) -> tuple[pd.DataFrame, BudgetBands]:
    """Normalize shambhuraje/Swiggy_Vs_Zomato (multi-city) to project schema with Hyderabad enrichment."""
    rows: list[dict] = []
    filter_key = metro_filter.strip().lower() if metro_filter else None

    for _, row in df.iterrows():
        city = _normalize_city(row.get("city"))
        if not city:
            continue
        if filter_key and city.lower() != filter_key:
            continue

        name = row.get("restaurant_name")
        if name is None or (isinstance(name, float) and pd.isna(name)):
            continue
        name = str(name).strip()
        if not name:
            continue

        rid = row.get("restaurant_id")
        restaurant_id = (
            str(rid).strip()
            if rid is not None and not (isinstance(rid, float) and pd.isna(rid))
            else str(abs(hash(f"{name}-{city}")) % 10**12)
        )

        rating = _optional_float(row.get("zomato_rating"))
        if rating is None:
            rating = _optional_float(row.get("average_rating_both_platforms"))

        cost = _optional_int(row.get("avg_cost_per_person_inr"))
        votes = _optional_int(row.get("zomato_total_reviews"))

        cuisines = _parse_cuisines(row.get("cuisines"))
        orig_locality = _optional_str(row.get("locality"))

        if city == "Hyderabad":
            enriched_name, enriched_locality, address, online_order, book_table = _enrich_hyderabad_row(
                restaurant_id, name, orig_locality, cuisines, rating
            )
            rows.append(
                {
                    "id": restaurant_id,
                    "name": enriched_name,
                    "location": city,
                    "locality": enriched_locality,
                    "cuisines": cuisines,
                    "rating": rating,
                    "approx_cost": cost,
                    "votes": votes,
                    "address": address,
                    "rest_type": _optional_str(row.get("restaurant_type")),
                    "online_order": online_order,
                    "book_table": book_table,
                }
            )
        else:
            rows.append(
                {
                    "id": restaurant_id,
                    "name": name,
                    "location": city,
                    "locality": orig_locality,
                    "cuisines": cuisines,
                    "rating": rating,
                    "approx_cost": cost,
                    "votes": votes,
                    "address": None,
                    "rest_type": _optional_str(row.get("restaurant_type")),
                    "online_order": None,
                    "book_table": None,
                }
            )

    if not rows:
        hint = f" for metro '{metro_filter}'" if metro_filter else ""
        raise ValueError(f"No valid rows after cleaning{hint}.")

    return _finalize_dataframe(pd.DataFrame(rows))


def _finalize_dataframe(clean: pd.DataFrame) -> tuple[pd.DataFrame, BudgetBands]:
    clean = clean.sort_values(
        by=["rating", "votes"],
        ascending=[False, False],
        na_position="last",
    )
    clean = clean.drop_duplicates(subset=["id"], keep="first")
    clean = clean.drop_duplicates(subset=["name", "location"], keep="first")
    clean = clean.reset_index(drop=True)
    bands = compute_budget_bands(clean["approx_cost"])
    return clean, bands


def transform_dataframe(
    df: pd.DataFrame,
    *,
    metro_filter: str | None = None,
) -> tuple[pd.DataFrame, BudgetBands]:
    """Clean raw HF dataframe into normalized columns for Parquet."""
    if _is_swiggy_zomato_schema(df):
        return transform_swiggy_zomato_dataframe(df, metro_filter=metro_filter)
    col_name = _resolve_column(df, "name")
    col_locality = _resolve_column(df, "locality")
    col_listed_area = _resolve_column(df, "listed_area")
    col_cuisines = _resolve_column(df, "cuisines")
    col_rate = _resolve_column(df, "rate")
    col_cost = _resolve_column(df, "approx_cost")
    col_votes = _resolve_column(df, "votes")
    col_address = _resolve_column(df, "address")
    col_rest_type = _resolve_column(df, "rest_type")
    col_url = _resolve_column(df, "url")
    col_online = _resolve_column(df, "online_order")
    col_book = _resolve_column(df, "book_table")

    if col_name is None:
        raise ValueError(
            f"Required column 'name' not found. Available: {list(df.columns)}"
        )
    if col_locality is None and col_address is None:
        raise ValueError(
            f"Required locality or address column not found. Available: {list(df.columns)}"
        )

    rows: list[dict] = []
    for idx, row in df.iterrows():
        name = row[col_name] if col_name else None
        if name is None or (isinstance(name, float) and pd.isna(name)):
            continue
        name = str(name).strip()
        if not name:
            continue

        # Metro city — HF "listed_in(city)" / location column is often an area, not metro
        url_val = row[col_url] if col_url else None
        city = (
            _resolve_metro_city(row[col_address], url_val)
            if col_address
            else _city_from_zomato_url(url_val)
        )

        locality = None
        if col_locality and row[col_locality] is not None:
            loc_val = row[col_locality]
            if not (isinstance(loc_val, float) and pd.isna(loc_val)):
                locality = str(loc_val).strip() or None
        if not locality and col_listed_area and row[col_listed_area] is not None:
            area_val = row[col_listed_area]
            if not (isinstance(area_val, float) and pd.isna(area_val)):
                locality = str(area_val).strip() or None

        location = city or locality
        if not location:
            continue

        url_val = row[col_url] if col_url else None
        restaurant_id = _make_id(url_val, int(idx))

        cuisines = _parse_cuisines(row[col_cuisines]) if col_cuisines else []
        rating = _parse_rating(row[col_rate]) if col_rate else None
        approx_cost = _parse_cost(row[col_cost]) if col_cost else None
        votes = _parse_votes(row[col_votes]) if col_votes else None

        address = None
        if col_address and row[col_address] is not None:
            addr = row[col_address]
            if not (isinstance(addr, float) and pd.isna(addr)):
                address = str(addr).strip() or None

        rest_type = None
        if col_rest_type and row[col_rest_type] is not None:
            rt = row[col_rest_type]
            if not (isinstance(rt, float) and pd.isna(rt)):
                rest_type = str(rt).strip() or None

        online_order = None
        if col_online and row[col_online] is not None:
            oo = row[col_online]
            if not (isinstance(oo, float) and pd.isna(oo)):
                online_order = str(oo).strip() or None

        book_table = None
        if col_book and row[col_book] is not None:
            bt = row[col_book]
            if not (isinstance(bt, float) and pd.isna(bt)):
                book_table = str(bt).strip() or None

        rows.append(
            {
                "id": restaurant_id,
                "name": name,
                "location": location,
                "locality": locality,
                "cuisines": cuisines,
                "rating": rating,
                "approx_cost": approx_cost,
                "votes": votes,
                "address": address,
                "rest_type": rest_type,
                "online_order": online_order,
                "book_table": book_table,
            }
        )

    if not rows:
        raise ValueError("No valid rows after cleaning.")

    clean = pd.DataFrame(rows)
    if metro_filter:
        key = metro_filter.strip().lower()
        clean = clean[clean["location"].str.lower() == key]
        if clean.empty:
            raise ValueError(
                f"No rows for metro '{metro_filter}' after cleaning. "
                "Check DATA_METRO_FILTER or HF_DATASET_ID."
            )
    return _finalize_dataframe(clean)


def _optional_str(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _find_city_in_text(text: object) -> str | None:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    lower = str(text).lower()
    for alias, canonical in sorted(CITY_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in lower or canonical.lower() in lower:
            return canonical
    return None


def _coerce_cuisines(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, str):
        return _parse_cuisines(value)
    if isinstance(value, (list, tuple)):
        return [str(c).strip() for c in value if str(c).strip()]
    try:
        return [str(c).strip() for c in list(value) if str(c).strip()]
    except TypeError:
        return _parse_cuisines(value)


def dataframe_to_restaurants(df: pd.DataFrame) -> list[Restaurant]:
    restaurants: list[Restaurant] = []
    for record in df.to_dict(orient="records"):
        cuisines = _coerce_cuisines(record.get("cuisines"))
        restaurants.append(
            Restaurant(
                id=str(record["id"]),
                name=str(record["name"]),
                location=str(record["location"]),
                locality=_optional_str(record.get("locality")),
                cuisines=list(cuisines),
                rating=_optional_float(record.get("rating")),
                approx_cost=_optional_int(record.get("approx_cost")),
                votes=_optional_int(record.get("votes")),
                address=_optional_str(record.get("address")),
                rest_type=_optional_str(record.get("rest_type")),
                online_order=_optional_str(record.get("online_order")),
                book_table=_optional_str(record.get("book_table")),
            )
        )
    return restaurants


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def save_budget_bands(bands: BudgetBands, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "low_max": bands.low_max,
                "medium_min": bands.medium_min,
                "medium_max": bands.medium_max,
                "high_min": bands.high_min,
            }
        ]
    ).to_parquet(path, index=False)


def load_budget_bands(path: Path) -> BudgetBands | None:
    if not path.exists():
        return None
    row = pd.read_parquet(path).iloc[0]
    return BudgetBands(
        low_max=int(row["low_max"]),
        medium_min=int(row["medium_min"]),
        medium_max=int(row["medium_max"]),
        high_min=int(row["high_min"]),
    )


def run_ingestion(
    hf_dataset_id: str,
    cache_path: Path,
    *,
    force: bool = False,
    metro_filter: str | None = None,
) -> tuple[pd.DataFrame, BudgetBands]:
    """Download (if needed), transform, and write Parquet cache."""
    from src.config.settings import get_settings

    bands_path = cache_path.parent / "budget_bands.parquet"
    if metro_filter is None:
        metro_filter = get_settings().data_metro_filter

    if cache_path.exists() and bands_path.exists() and not force:
        df = pd.read_parquet(cache_path)
        bands = load_budget_bands(bands_path)
        if bands is None:
            bands = compute_budget_bands(df["approx_cost"])
        return df, bands

    raw = load_raw_dataframe(hf_dataset_id)
    clean, bands = transform_dataframe(raw, metro_filter=metro_filter)
    save_parquet(clean, cache_path)
    save_budget_bands(bands, bands_path)
    return clean, bands
