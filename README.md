# SmartHire

AI-powered screening & interview tracking portal. A single monolithic web app that runs the
full hiring loop — **JD creation → AI résumé screening → timed rubric Q&A → weighted score
fusion → interviewer decision → audit** — where **AI scores, humans decide**.

- **Backend:** Python + FastAPI, SQLAlchemy, in-memory SQLite, provider-agnostic LLM wrapper.
- **Frontend:** React + Vite + Tailwind (role-based portals: Admin / Candidate / Interviewer).
- **LLM:** runs fully **offline with a deterministic mock** by default; switch to OpenAI or
  Anthropic by setting `.env`.
- **Seed data:** `input-data.json` (3 JDs, 18 rubric questions, 10 synthetic résumés, 14 users).

---

## Project layout

```
smart-hire-python/
├── backend/
│   ├── main.py                 # FastAPI app + lifespan (init DB + seed)
│   ├── config.py               # env-driven settings
│   ├── database.py             # SQLAlchemy engine/session (in-memory SQLite)
│   ├── seed.py                 # loads input-data.json
│   ├── models/                 # ORM entities
│   ├── schemas/                # Pydantic DTOs + LLM output schemas
│   ├── repositories/           # data access
│   ├── services/               # business logic (JD, screening, Q&A, fusion, interview, flags)
│   ├── ai/                     # llm_client + resume_match + answer_score (+ mock heuristics)
│   ├── auth/                   # JWT-style tokens + role deps
│   ├── audit/                  # audit event recorder
│   ├── api/                    # REST routers
│   └── tests/                  # pytest suite
├── frontend/
│   └── src/
│       ├── components/         # Layout, ui primitives, ProtectedRoute
│       ├── context/            # AuthContext
│       ├── services/           # api client
│       └── pages/              # Login, Admin/*, Candidate/*, Interviewer/*
├── input-data.json             # synthetic seed data
├── .env.example
└── docker-compose.yml
```

---

## Quick start

### Option A — Docker Compose

```bash
cd smart-hire-python
cp .env.example .env          # LLM_PROVIDER=mock by default
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### Option B — local dev

Backend:

```bash
cd smart-hire-python/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload --port 8000
```

Frontend (new terminal):

```bash
cd smart-hire-python/frontend
npm install
npm run dev            # http://localhost:5173 (proxies /api -> :8000)
```

---

## Demo credentials

| Role        | Username       | Password   |
|-------------|----------------|------------|
| Admin       | `admin1` / `admin2` | `admin123` |
| Candidate   | `candidate1` … `candidate10` | `cand123` |
| Interviewer | `interviewer1` / `interviewer2` | `int123` |

**Try the full loop:** sign in as `admin1` → Job Descriptions → **Run** on *Frontend Developer*
→ sign out → sign in as `candidate1` (Aarav Sharma) → **Start screening Q&A** → answer the 6
questions → sign out → `admin1` → Candidates → open *Aarav Sharma* → set **Next steps** /
**Send invitation** / **Assign interviewer** → sign out → `interviewer1` → **Review** →
**Record decision** (Accepted / Rejected / On-Hold / No-show).

---

## LLM configuration

`backend/ai/llm_client.py` is provider-agnostic. Two logical prompts only:
`resume_match` and `answer_score`.

| `.env`                     | Behaviour                                             |
|----------------------------|-------------------------------------------------------|
| `LLM_PROVIDER=mock`        | Deterministic offline heuristics (default, no key)    |
| `LLM_PROVIDER=openai`      | Uses `LLM_API_KEY` + `LLM_BASE_URL` + `LLM_MODEL`     |
| `LLM_PROVIDER=anthropic`   | Uses `LLM_API_KEY` + `LLM_MODEL`                      |

**Guardrails:** every LLM response is validated against a Pydantic schema; invalid JSON is
retried **exactly once** with a correction instruction; still invalid → controlled `LLMError`.
No uncontrolled retry loops. Prompts/justifications never appear in the candidate UI.

---

## API (prefix `/api`)

| Method | Endpoint | Role |
|---|---|---|
| POST | `/login`, GET `/me` | Public / Any |
| GET/POST | `/jds` | Admin |
| GET/PUT/DELETE | `/jds/{id}` | Admin |
| POST | `/jds/{id}/resume-score` | Admin (on-demand per JD) |
| GET | `/candidates`, `/candidates/{id}` | Admin / Interviewer (assigned) |
| GET | `/applications`, `/applications/mine` | Admin / Candidate |
| GET | `/applications/{id}` | Authorized role (includes telemetry summary) |
| GET | `/applications/{id}/questions` | Candidate (owner) |
| POST | `/applications/{id}/answers` | Candidate (owner; `time_spent_seconds` + telemetry) |
| POST | `/applications/{id}/telemetry` | Candidate (owner) |
| POST | `/applications/{id}/assign-interviewer` | Admin |
| POST | `/applications/{id}/next-steps` | Admin |
| POST | `/applications/{id}/invite` | Admin (stubbed) |
| POST | `/applications/{id}/decision` | Interviewer (ACCEPTED/REJECTED/ON_HOLD/NO_SHOW) |
| POST | `/applications/{id}/notes` | Interviewer / Admin |
| GET | `/interviewer/assignments` | Interviewer |
| GET | `/audit`, `/flags`, `/dashboard`, `/users/interviewers` | Admin |

---

## Tests

```bash
cd smart-hire-python/backend
source .venv/bin/activate
pytest -q
```

Covers: LLM wrapper (valid / malformed / schema mismatch / retry-then-fail), normalization,
weighted fusion, PASS/HOLD/REJECT boundaries, résumé + answer heuristics, seed loading from
`input-data.json`, role enforcement, JD CRUD, screening → Q&A flow, candidate interview info,
decision vocabulary, next-steps/invitation stub, telemetry counters, and cross-role authorization.

---

## Design decisions

- **HOLD band:** `PASS` if `combined ≥ pass_threshold`; `REJECT` if `combined < threshold − hold_margin`
  (default 15); else `HOLD`.
- **0–5 → 0–100 normalization:** linear (`score / 5 × 100`).
- **Screening trigger:** on-demand per JD from the Admin (not a background daemon).
- **Statuses:** `APPLIED → SCREENING → PASSED/HOLD/REJECTED → INTERVIEW → ACCEPTED/REJECTED/ON_HOLD/NO_SHOW`
  (plus `ARCHIVED` for below-threshold).
- **Rubric bands** (`score_5`/`score_3`/`score_0`) from `input-data.json` drive `answer_score`.
- **Update/Delete JDs:** `PUT`/`DELETE /jds/{id}` added (spec labelled JD CRUD but listed only create/read).
- **Extra columns for explainability:** `JobDescription.education`, `Application.resume_evidence`
  / `qa_confidence`, `Answer.justification` / `time_spent_seconds`.
- **Next steps & invitation:** editable free-text "Next steps" and a **stubbed invitation**
  (in-app toast + `invitation.sent` audit event — no real email/SMS).
- **Anti-cheat:** client-captured tab-switch / paste / question-copy events, surfaced only to
  Admin/Interviewer as counters and flags; never used for auto-reject.

## Out of scope / not implemented

Résumé file upload & parsing (PDF/DOCX→JSON), candidate self-registration, real email/SMS,
external queues/infrastructure — consistent with the source specification. The mock provider
cannot detect résumé over-claims (e.g. contradictory experience); the real LLM provider does.