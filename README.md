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

## Production Deployment Guide

This project is optimized for deployment to production platforms like **Heroku**, **Render**, or **Streamlit Community Cloud**.

### 1. Pre-built Parquet Dataset Strategy (Zero Cold-Start Downloads)
To avoid downloading a massive **574 MB** dataset from Hugging Face at server startup (which will trigger platform startup timeouts and cold-start latency), this repository is configured to track processed Parquet files directly in Git:
* The pre-processed Parquet files are tiny (~582 KB).
* They are tracked in Git via updated `.gitignore` rules.
* On startup, the server automatically reads the pre-built files (`data/processed/restaurants.parquet` and `data/processed/budget_bands.parquet`) instantly, ensuring an immediate startup time.

### 2. Environment Variables Configuration
Configure the following environment variables in your deployment platform's Secrets or Config Vars:

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your live Groq API key | `gsk_...` |
| `LLM_PROVIDER` | AI provider (defaults to `groq`) | `groq` |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | `https://zomato-ai-frontend.vercel.app` |
| `NEXT_PUBLIC_API_URL` | Frontend env mapping to the backend API URL | `https://zomato-ai-backend.onrender.com` |

### 3. Deploying the Backend API (FastAPI)
Deploy the root repository to a backend service provider (like Heroku or Render):
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** The `Procfile` is pre-configured to run the optimized startup command:
  ```bash
  python scripts/download_dataset.py && uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
  ```
  *(Without the `--force` flag, it boots instantly by using the pre-built Git-tracked Parquet file.)*

### 4. Deploying the Frontend (Next.js)
Deploy the `/frontend` directory to **Vercel** or **Netlify**:
* **Root Directory:** `frontend`
* **Build Command:** `npm run build`
* **Start Command:** `npm run start`
* **Environment Variables:** Set `NEXT_PUBLIC_API_URL` pointing to your deployed FastAPI backend URL.
