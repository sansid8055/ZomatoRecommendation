# Project Context: AI-Powered Restaurant Recommendation System

> **Source:** `Problem statement.docx` (Zomato use case)  
> **Workspace:** `Zomato recommd`  
> **Last captured:** 2026-05-20

---

## Overview

Build an **AI-powered restaurant recommendation service** inspired by **Zomato**. The system should intelligently suggest restaurants based on user preferences by **combining structured restaurant data with a Large Language Model (LLM)** to produce personalized, human-like recommendations.

---

## Objective

Design and implement an application that:

1. **Accepts user preferences** — location, budget, cuisine, ratings, and other constraints
2. **Uses a real-world restaurant dataset** — Zomato data from Hugging Face
3. **Leverages an LLM** — to generate personalized, natural-language recommendations
4. **Displays clear, useful results** — ranked options with explanations

---

## Data Source

| Item | Detail |
|------|--------|
| **Dataset (default)** | [shambhuraje/Swiggy_Vs_Zomato](https://huggingface.co/datasets/shambhuraje/Swiggy_Vs_Zomato) — filtered to **Hyderabad** on ingest |
| **Legacy dataset** | [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) (Bangalore-only) |
| **Scale (cache)** | ~240 Hyderabad restaurants |
| **Fields to extract** | Restaurant name, location, cuisine, cost, rating, and related attributes |

### Data ingestion responsibilities

- Load and preprocess the dataset from Hugging Face
- Extract and normalize relevant fields for filtering and LLM prompts
- Prepare structured subsets that match user criteria before LLM invocation

---

## System Workflow

```
User Preferences → Filter Dataset → Structured Candidates → LLM Prompt → Ranked Recommendations → UI Output
```

### 1. Data ingestion

- Load the Zomato dataset from Hugging Face
- Preprocess and select fields: name, location, cuisine, cost, rating, etc.

### 2. User input

Collect preferences from the user:

| Preference | Examples / format |
|------------|---------------------|
| **Location** | Hyderabad, Delhi, Bangalore, … |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional** | family-friendly, quick service, etc. |

### 3. Integration layer

- Filter restaurant data based on user input
- Prepare a structured candidate list for the LLM
- Design prompts so the LLM can **reason**, **rank**, and **explain** choices

### 4. Recommendation engine (LLM)

The LLM should:

- **Rank** restaurants relative to user preferences
- **Explain** why each recommendation fits
- **Optionally summarize** the overall set of choices

### 5. Output display

Present top recommendations in a user-friendly format. Each result should include:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- **AI-generated explanation** (why it was recommended)

---

## Technical Implications

| Layer | Role |
|-------|------|
| **Data pipeline** | Hugging Face load, cleaning, field mapping, pre-filtering |
| **Preference handling** | Form or API for location, budget, cuisine, rating, extras |
| **Filtering logic** | Rule-based narrowing before LLM (cost bands, location, cuisine, min rating) |
| **Prompt design** | Structured context + user prefs → ranking + explanations |
| **LLM integration** | API or local model for ranking, explanation, optional summary |
| **Presentation** | UI or CLI showing top N results with all required fields |

---

## Success Criteria

- Recommendations are **grounded in real dataset rows** (not hallucinated restaurants)
- Output is **personalized** to stated preferences
- Each recommendation includes a **clear, human-readable rationale**
- Results are **easy to scan** (name, cuisine, rating, cost, explanation)

---

## Out of Scope (not specified in problem statement)

- Authentication, payments, or booking
- Real-time Zomato API integration
- Specific tech stack (Python/Node, Streamlit/Flask/React, LLM provider)
- Exact number of recommendations to return
- Evaluation metrics or test requirements

These can be decided during implementation unless provided by course or mentor guidelines.

---

## Reference

- Problem statement document: `c:\Users\sanov\Downloads\Problem statement.docx`
- Local copy: `Docs/problemStatement.txt`
- Dataset: https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation
