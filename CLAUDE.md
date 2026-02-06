# Sovereign Audit - Development Guidelines

## Project Overview

EU Data Sovereignty Auditor: a FastAPI backend + React (Vite) frontend that analyzes SaaS websites for data sovereignty risks. The backend scrapes pages, detects third-party services, calls Gemini AI for analysis, and calculates a sovereignty score (0-100).

## Architecture

- **Backend**: `backend/main.py` — single-file FastAPI app. Gemini AI for analysis, `known_services.json` for service fingerprinting.
- **Frontend**: `frontend/src/` — React + Vite + Tailwind. Components: `Hero.jsx` (search input), `Loading.jsx` (5-step progress), `Dashboard.jsx` (results display).
- **API**: `POST /analyze` with `{ "url": "..." }` body. Returns `AnalyzeResponse` with score, vendors, infrastructure, compliance, detected services, etc.

## Dummy Mode (UI Testing Without LLM Calls)

Type **`dummy`** in the search box to get a full mock response instantly — no scraping, no Gemini API calls. This exercises every section of the Dashboard UI:

- Score card (42/100, High risk)
- Executive summary
- 14 risk factors
- Company info (EU registration, 3 office locations, employee locations)
- Infrastructure (AWS, Fly.io, 2 data centers, 2 server locations, 2 CDN providers)
- Data flows (EU + US storage, Global residency)
- Compliance (GDPR status, 3 certifications, data residency guarantees, 1 recent incident)
- 5 detected services (with EU alternatives and notes)
- Additional findings (3 recent changes, search summary, additional categories)
- 12 vendors in the sub-processors table (mix of Critical/High/Medium/Low risks)

**When adding new features to the Dashboard or response model, update the dummy response in `backend/main.py`** (search for `DUMMY MODE`) so it remains representative.

## Key Patterns

- Pydantic models define the API contract (`AnalyzeResponse`, `InfrastructureInfo`, etc.) — when Gemini returns `null` for string fields, use `or "Unknown"` not `.get("key", "Unknown")` to handle explicit `None` values.
- Scoring logic is in `calculate_score()` with category-based weights in `CATEGORY_WEIGHTS`.
- Service detection uses both `known_services.json` (fingerprinting) and Gemini AI (inference from page content).
- Thread pool (`ThreadPoolExecutor`) wraps blocking calls; `_*_safe` wrappers catch exceptions for thread pool compatibility.

## Running Locally

```bash
# Backend
cd backend && pip install -r requirements.txt
cp .env.example .env  # add GEMINI_API_KEY
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Testing

Use `dummy` for UI work. For real API testing, see `docs/TESTING_GUIDE.md` for example URLs (intercom.com, stripe.com, openai.com).
