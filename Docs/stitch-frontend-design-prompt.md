# Google Stitch — Frontend Design Prompt

Copy everything below the line into Google Stitch.

---

## Product

Design a **modern, polished web UI** for **“Zomato AI Restaurant Recommendations”** — an AI-powered restaurant discovery app inspired by Zomato (not a clone). Users set preferences; the app filters ~51k real restaurants from a Hugging Face dataset, then an LLM (Groq) ranks results and writes personalized explanations. **No auth, payments, or booking** — discovery and recommendations only.

**Brand feel:** Food-delivery / dining discovery — trustworthy, appetizing, mobile-first but desktop-friendly. Reference Zomato’s clarity (strong hierarchy, rating/cost chips, card-based listings) without copying their exact branding. Use a distinct primary accent (e.g. deep red/coral or warm orange) plus neutral surfaces.

**Target:** Portfolio demo + course submission — should look production-quality, not a default form template.

---

## User flow (must support all states)

```
Landing / Search Form → Submit → Loading (5–15s LLM) → Results OR Empty State
Results → “Refine search” → back to form (preserve or reset prefs)
```

1. **Landing / preferences** — hero + compact preference panel  
2. **Loading** — full-width or inline spinner with copy: “Finding recommendations… (may take 5–15 seconds)”  
3. **Success** — optional AI summary + up to **5 ranked restaurant cards**  
4. **Empty** — no matches: friendly message + bullet suggestions (lower rating, broader cuisine, different budget, larger city)  
5. **Error** — missing API key, dataset missing, or request failed: clear `st.error`-style alert with recovery steps  
6. **Degraded mode** — info banner when AI ranking failed but rule-based top picks are shown  

---

## Screens & layout

### Screen 1: Home / Get recommendations

**Header**
- App name: “Zomato AI Restaurant Recommendations”
- Subtitle: “Personalized picks from real Zomato data — filtered locally, ranked by AI”
- Optional small badge: “Powered by Groq AI”

**Main column (centered, max-width ~720–960px)**

**Preference form** — single card or elevated panel:

| Field | Control | Notes |
|-------|---------|--------|
| Location | Searchable dropdown | Cities from dataset (default **Hyderabad**; multi-city HF source) |
| Budget | Segmented control / 3 pills | `low` · `medium` · `high` with short helper: “Based on cost-for-two bands” |
| Cuisine | Text input with placeholder | e.g. “Italian, Chinese, North Indian” — optional |
| Minimum rating | Slider 0.0–5.0, step 0.5 | Default 4.0; label “Set to 0 to skip” |
| Additional preferences | Multiline textarea | e.g. “family-friendly, quick service, rooftop” — optional, max ~500 chars |

**Primary CTA:** “Get recommendations” — full width on mobile, prominent button.

**Sidebar (desktop) / drawer or bottom sheet (mobile): “Setup”**
- Status: “API key configured” (green) OR error with link hint to Groq Console
- Read-only chips: Model name, Provider, Top K (5)
- Secondary button: “Refine search” (clears results, returns focus to form)

**Empty hint (before first search):** Info callout — “Select your preferences and click Get recommendations to see personalized cards with AI explanations.”

---

### Screen 2: Results

**Section header:** “Your recommendations”

**Optional AI summary** — success-style banner, 1–2 sentences overview of the picks.

**Metadata line (subtle):** “5 recommendations (from X matches, Y sent to AI)”

**Degraded mode banner (conditional):** Info style — “Showing top-rated matches (AI ranking unavailable).”

**Recommendation cards (×5)** — vertical stack, each card includes:

| Element | Content |
|---------|---------|
| Rank badge | “#1 Recommendation” … “#5” |
| Title | Restaurant name (truncate long names gracefully) |
| Meta row | Cuisine · Rating (e.g. 4.3 / 5) · Cost (₹550 for two) · Location + locality |
| Explanation | Expandable section **“Why we recommend this”** — 2–3 sentences, readable line length |

**Card design:** Soft shadow, rounded corners (12–16px), clear separation; rating as star or numeric chip; cost in INR; optional cuisine tags.

**Do not** show duplicate chain names in the list (design should assume unique restaurants per card).

---

### Screen 3: Empty state

- Warning/empty illustration (simple line art or icon)
- Headline: “No restaurants match your criteria”
- Body: dataset-grounded message
- **“Try:”** bullet list:
  - Lowering the minimum rating
  - Choosing a broader cuisine (or leave blank)
  - Switching budget to medium or high
  - Picking a larger city from the list

---

### Screen 4: Error states

Design variants for:
- **GROQ_API_KEY missing** — blocking setup in sidebar + inline error on submit
- **Dataset not found** — “Run download script” with monospace command hint
- **Request failed** — generic error with retry affordance

---

## Visual & UX guidelines

- **Typography:** Modern sans (e.g. Inter, DM Sans, or similar); clear H1/H2/body scale  
- **Color:** Light mode primary; optional dark mode variant. High contrast for text; WCAG-friendly  
- **Spacing:** Generous padding in cards; 8px grid  
- **Icons:** Location pin, star rating, currency (₹), cuisine/utensils, sparkles/AI for summary  
- **Motion:** Subtle loading skeleton for cards; spinner during LLM wait  
- **Accessibility:** Labels on all inputs, focus states, sufficient touch targets (44px) on mobile  

---

## Data contract (for realistic mock content)

Use this structure in mocks:

**User input**
```json
{
  "location": "Hyderabad",
  "budget": "medium",
  "cuisine": "Chinese",
  "min_rating": 4.0,
  "additional_preferences": "family-friendly, quick service"
}
```

**Each recommendation card**
```json
{
  "rank": 1,
  "name": "Green Onion",
  "cuisine": "Chinese",
  "rating": 4.3,
  "approx_cost": 550,
  "location": "Hyderabad",
  "locality": "Residency Road",
  "explanation": "A top choice for Chinese cuisine in Hyderabad with a 4.3 rating and ₹550 for two, fitting your medium budget..."
}
```

**Summary (optional)**
```json
{
  "summary": "Top Chinese picks in Hyderabad for a medium budget — mix of dedicated Chinese spots and highly rated options."
}
```

**Sample cities for dropdown:** Hyderabad (default), Delhi, Mumbai, Bangalore, Chennai, Kolkata, Pune.

---

## Technical context (for handoff)

- **Website stack:** **Next.js 14** (React, TypeScript, Tailwind) frontend + **FastAPI** backend (`src/api/main.py`)
- Design as **responsive web app** (desktop 1280px + mobile 390px), not native mobile OS chrome
- Legacy Streamlit UI remains at `src/app/main.py` for quick demos  
- Backend returns max **5** recommendations; filter cap ~25 before LLM  
- Currency: **INR**, “for two”  
- India-centric locations and copy  

---

## Deliverables requested from Stitch

1. **Desktop** (1440px) — home with form + results below  
2. **Mobile** (390px) — stacked form, sticky CTA, scrollable cards  
3. **Component library:** buttons, inputs, slider, budget pills, recommendation card, summary banner, empty state, error alert, loading state  
4. **Design tokens:** color, type, radius, shadow, spacing  
5. Optional: dark mode frame  

**Avoid:** cluttered dashboards, maps, photo carousels (no images in dataset), login/signup, cart, or checkout flows.

---

## Success criteria (design must make these obvious)

- Recommendations are **easy to scan** — name, cuisine, rating, cost visible at a glance  
- **AI explanation** is the differentiator — visually emphasized but not overwhelming  
- Form feels **fast and simple** — 5 fields, one primary action  
- **Trust signals:** “real Zomato data”, “AI-ranked”, match counts in metadata  

Generate high-fidelity mockups and reusable components suitable for developer handoff to React or a custom Streamlit theme.
