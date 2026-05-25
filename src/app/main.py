"""
Zomato AI Restaurant Recommendations — Streamlit UI (Phase 5).

Run from project root:
    streamlit run src/app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path when launched via Streamlit
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
from pydantic import ValidationError

from src.config.settings import get_settings
from src.data.models import UserPreferences
from src.data.repository import RestaurantRepository
from src.services.orchestrator import RecommendationOrchestrator
from src.services.schemas import RankedRecommendation, RecommendationResponse

PAGE_TITLE = "Zomato AI Restaurant Recommendations"
PAGE_ICON = "🍽️"

CUSTOM_CSS = """
<style>
    .rec-card {
        padding: 1rem 1.25rem;
        border-radius: 0.5rem;
        border: 1px solid rgba(128, 128, 128, 0.35);
        margin-bottom: 1rem;
        background: rgba(255, 255, 255, 0.02);
    }
    .rec-rank {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 0.25rem;
    }
    .rec-meta {
        font-size: 0.95rem;
        color: #ccc;
    }
</style>
"""


@st.cache_resource(show_spinner="Loading restaurant dataset…")
def load_app() -> tuple[RestaurantRepository, RecommendationOrchestrator]:
    """Warm up repository once per server process (UI-01)."""
    repo = RestaurantRepository()
    repo.load()
    return repo, RecommendationOrchestrator(repository=repo)


def _api_key_configured() -> bool:
    settings = get_settings()
    return bool(settings.groq_api_key and str(settings.groq_api_key).strip())


def _truncate(text: str, max_len: int = 80) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _format_cost(cost: int | None) -> str:
    if cost is None:
        return "Cost not available"
    return f"₹{cost:,} for two"


def _format_rating(rating: float | None) -> str:
    if rating is None:
        return "Rating not available"
    return f"{rating:.1f} / 5"


def _init_session_state() -> None:
    defaults = {
        "last_response": None,
        "loading": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_preference_form(locations: list[str]) -> UserPreferences | None:
    """Preference form; returns UserPreferences on submit, else None."""
    with st.form("preference_form", clear_on_submit=False):
        st.subheader("Your preferences")

        if not locations:
            st.error("No locations available. Check dataset setup.")
            st.form_submit_button("Get recommendations", disabled=True)
            return None

        settings = get_settings()
        preferred = settings.default_metro_city
        default_location = (
            preferred
            if preferred in locations
            else locations[0]
        )
        location = st.selectbox(
            "Location",
            options=locations,
            index=locations.index(default_location),
            help="City or area from the dataset",
        )

        budget = st.radio(
            "Budget",
            options=["low", "medium", "high"],
            index=1,
            horizontal=True,
            help="Based on cost-for-two bands from the dataset",
        )

        cuisine = st.text_input(
            "Cuisine (optional)",
            placeholder="e.g. Italian, Chinese, North Indian",
            max_chars=100,
        )

        min_rating = st.slider(
            "Minimum rating",
            min_value=0.0,
            max_value=5.0,
            value=4.0,
            step=0.5,
            help="Set to 0 to skip rating filter",
        )

        additional = st.text_area(
            "Additional preferences (optional)",
            placeholder="e.g. family-friendly, quick service, rooftop",
            max_chars=500,
            height=80,
        )

        submitted = st.form_submit_button(
            "Get recommendations",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.get("loading", False),
        )

    if not submitted:
        return None

    try:
        return UserPreferences(
            location=location,
            budget=budget,  # type: ignore[arg-type]
            cuisine=cuisine.strip() or None,
            min_rating=min_rating if min_rating > 0 else None,
            additional_preferences=additional.strip() or None,
        )
    except ValidationError as exc:
        st.error(f"Invalid preferences: {exc}")
        return None


def _render_recommendation_card(rec: RankedRecommendation) -> None:
    name = _truncate(rec.name)
    locality = f" · {rec.locality}" if rec.locality else ""
    st.markdown(
        f'<div class="rec-card">'
        f'<div class="rec-rank">#{rec.rank} Recommendation</div>'
        f"<h3>{name}</h3>"
        f'<p class="rec-meta"><strong>Cuisine:</strong> {rec.cuisine}<br/>'
        f"<strong>Rating:</strong> {_format_rating(rec.rating)}<br/>"
        f"<strong>Cost:</strong> {_format_cost(rec.approx_cost)}<br/>"
        f"<strong>Location:</strong> {rec.location}{locality}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    with st.expander("Why we recommend this", expanded=True):
        st.write(rec.explanation)


def _render_results(response: RecommendationResponse) -> None:
    if not response.success:
        st.error(response.message or "Something went wrong.")
        return

    if not response.recommendations:
        st.warning(response.message or "No restaurants match your criteria.")
        if response.suggestions:
            st.markdown("**Try:**")
            for tip in response.suggestions:
                st.markdown(f"- {tip}")
        return

    if response.summary:
        st.success(response.summary)

    if response.metadata.degraded_mode:
        st.info(
            response.message
            or "Showing top-rated matches (AI ranking unavailable)."
        )

    st.markdown(f"**{len(response.recommendations)} recommendations** "
                f"(from {response.metadata.total_matched} matches, "
                f"{response.metadata.candidate_count} sent to AI)")

    for rec in response.recommendations:
        _render_recommendation_card(rec)


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    _init_session_state()

    st.title("🍽️ Zomato AI Restaurant Recommendations")
    st.caption(
        "Personalized picks from real Zomato data — filtered locally, ranked by Groq AI."
    )

    settings = get_settings()

    # --- Sidebar: setup & config ---
    with st.sidebar:
        st.header("Setup")
        if not settings.data_cache_path.exists():
            st.error(
                "Dataset not found. Run:\n\n"
                "`python scripts/download_dataset.py`"
            )
            st.stop()

        if not _api_key_configured():
            st.error(
                "GROQ_API_KEY is not set.\n\n"
                "Copy `.env.example` to `.env` and add your key from "
                "[Groq Console](https://console.groq.com/keys)."
            )
            st.stop()

        st.success("API key configured")
        st.markdown(f"**Model:** `{settings.llm_model}`")
        st.markdown(f"**Provider:** `{settings.llm_provider}`")
        st.markdown(f"**Top K:** {settings.top_k_results}")

        if st.button("Refine search", use_container_width=True):
            st.session_state.last_response = None
            st.rerun()

    # --- Load data ---
    try:
        repository, orchestrator = load_app()
    except Exception as exc:
        st.error(f"Failed to load restaurant data: {exc}")
        st.markdown(
            "See README: run `python scripts/download_dataset.py` first."
        )
        st.stop()

    locations = repository.get_available_locations()
    if not locations:
        st.error("No locations in dataset.")
        st.stop()

    # --- Form ---
    prefs = _render_preference_form(locations)

    if prefs is not None:
        st.session_state.loading = True
        with st.spinner("Finding recommendations… (may take 5–15 seconds)"):
            try:
                response = orchestrator.get_recommendations(
                    prefs,
                    fail_without_api_key=True,
                )
                st.session_state.last_response = response
            except Exception as exc:
                st.session_state.last_response = None
                st.error(f"Request failed: {exc}")
            finally:
                st.session_state.loading = False

    # --- Results (persist across reruns until refine) ---
    if st.session_state.last_response is not None:
        st.divider()
        st.subheader("Your recommendations")
        _render_results(st.session_state.last_response)
    else:
        st.info(
            "Select your preferences and click **Get recommendations** to see "
            "personalized restaurant cards with AI explanations."
        )


if __name__ == "__main__":
    main()
