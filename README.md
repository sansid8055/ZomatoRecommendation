# Zomato AI Restaurant Recommendation

AI-powered restaurant recommendations using the Zomato Hugging Face dataset and an LLM for ranking and explanations.

## Prerequisites

- Python 3.10+
- ~2 GB free disk (dataset + cache)
- Internet for first-time dataset download

## Setup

```bash
cd "d:\Nextleap\Zomato recommd"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Phase 1: Download & process data

```bash
python scripts/download_dataset.py
python scripts/smoke_test_data.py
```

## Phase 2: Filter pipeline

Deterministic filters (location → rating → cuisine → budget → sort & cap) before any LLM call. Empty matches return suggestions and **do not** invoke the LLM.

```bash
python -m src.domain.filters --location Bangalore --budget medium --cuisine Italian --min-rating 4
# or
python scripts/filter_probe.py --location Bangalore --budget medium --cuisine Italian --min-rating 4
python scripts/smoke_test_filters.py
```

## Phase 3: LLM ranking (Groq)

Uses [Groq](https://console.groq.com/) for fast inference. Set `GROQ_API_KEY` in `.env` for live calls; mock mode works without a key.

```bash
pip install groq
python scripts/smoke_test_llm.py
python scripts/test_llm_integration.py
python scripts/test_llm_integration.py --live
```

**Degraded mode:** If the LLM fails twice (bad JSON / API error), the engine falls back to rule-based top-K with template explanations.

**Components:** `src/llm/client.py` (Groq + mock), `prompts.py`, `parser.py`, `engine.py`.

## Phase 4: Orchestration

Single entry point: `get_recommendations(prefs)` wires filter → LLM → enrich.

```bash
python scripts/get_recommendations.py --location Bangalore --budget medium --cuisine Chinese --min-rating 4 --mock
python scripts/get_recommendations.py --location Bangalore --budget medium --cuisine Italian --min-rating 4
pytest tests/test_orchestrator.py -v
```

**Components:** `src/services/orchestrator.py`, `src/services/schemas.py`

## Phase 5: Web UI (Next.js + FastAPI) — recommended

Production-style website matching the **Gourmet Intelligence** Stitch design (`stitch_zomato_ai_restaurant_scout/`).

| Layer | Stack | Path |
|-------|--------|------|
| **Frontend** | Next.js 14, React, TypeScript, Tailwind | `frontend/` |
| **Backend API** | FastAPI, Uvicorn | `src/api/main.py` |

**Terminal 1 — API (port 8000):**

```bash
venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_api.py
```

**Terminal 2 — Frontend (port 3000):**

```bash
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000**. Set `GROQ_API_KEY` in the project root `.env` (API reads the same file).

Design reference: `Docs/stitch-frontend-design-prompt.md` and `stitch_zomato_ai_restaurant_scout/`.

## Phase 5 (alt): Streamlit app

Legacy quick UI:

```bash
streamlit run src/app/main.py
```

Requires processed data (`scripts/download_dataset.py`) and `GROQ_API_KEY` in `.env`.

Expected:

- `data/processed/restaurants.parquet` (~51k Bangalore rows from HF)
- Smoke test prints Bangalore matches and **PASSED**

## Run tests

```bash
pytest tests/ -v
```

## Project docs

- [context.md](Docs/context.md)
- [architecture.md](Docs/architecture.md)
- [implementation-plan.md](Docs/implementation-plan.md)
- [edge-cases.md](Docs/edge-cases.md)
- [data-schema.md](Docs/data-schema.md)

## Configuration

See `.env.example` for `DATA_CACHE_PATH`, `HF_DATASET_ID`, `DATA_METRO_FILTER` (default `Bangalore`), and LLM settings.
