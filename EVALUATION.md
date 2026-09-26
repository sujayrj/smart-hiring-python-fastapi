# SmartHire — Evaluation Handbook

> Single consolidated evaluation document.
>
> - **Part A — Project Requirements & FAQ** (context, success metrics, dataset, plus an FAQ).
>   Safe to share with the team.
> - **Part B — Mentor Intern Interview Guide**: question bank, answer keys, tricky questions,
>   tracks and scorecard. **CONFIDENTIAL — do not share with candidates.**
>
> For setup/run instructions see **[README.md](README.md)**.

---

## A1. Problem statement & background

Hiring is broken across two stages, and no existing tool covers both end to end: recruiters
drown in résumés, while interview coordination lives in scattered email threads. Strong
candidates get missed, weak ones reach expensive interview panels, and there is no single
source of truth for status, evidence or accountability. A single portal that chains AI-driven
screening with role-based interview tracking fixes both problems at once.

### Problem → what we solve

| Problem | What SmartHire does |
|---|---|
| Hundreds of résumés, no reliable filter | Every résumé auto-matched to the JD with an **explainable score, matched skills and gaps** |
| Manual, inconsistent conceptual screening | A short **AI-graded free-text Q&A round** with rubric-based scoring, justification and confidence — the same yardstick for everyone |
| Interview coordination trapped in email | **Role-based dashboards** for Hiring Manager and Interviewer replace inbox chaos |
| No live view of candidate status | One-click status updates (**Accepted / Rejected / On-Hold / No-show**), interviewer notes and "Next steps" logged per candidate |
| Slow funnel, poor candidate experience | Time-to-shortlist cut from days to minutes; every decision **auditable** |

---

## A2. Objective

Build a role-based web app that runs the end-to-end screening funnel from one place, with a
dedicated portal for each user type:

- **Hiring Manager (Admin) Portal** — feed the job description (role, must-have skills,
  experience, education); every incoming résumé is auto-scored against the JD by an AI call.
  Above-threshold candidates advance to screening; the rest are archived **with a reason**.
  The Admin sees the full pipeline dashboard, assigns interviews, logs "Next steps" and drills
  into all AI evidence.
- **Candidate Portal** — screened candidates are auto-invited into a short AI-graded free-text
  Q&A round with a per-question timer and anti-cheat signals. Each answer is scored via a
  rubric-based AI call (score, justification, confidence); the candidate sees their aggregate
  **PASS / HOLD / REJECT** band and can log in anytime to check live application status.
- **Interviewer Portal** — sees only assigned candidates with AI evidence attached, and submits
  structured decisions (**Accepted / Rejected / On-Hold / No-show**) with notes after the interview.

**Single source of truth** — every candidate's live status is visible on the Admin dashboard,
sortable, filterable and fully auditable; résumé-match and Q&A signals are fused into one
combined band with justification and confidence.

---

## A3. End-to-end workflow

```
Job creation → Résumé parsing (Score 1) → Test link (Score 2) → Interview (Score 3)
            → Final total score → Hiring Manager decision
```

1. **Seed at startup** — `input-data.json` is loaded into in-memory SQLite (users, JDs, questions, candidates + applications).
2. **Job creation** — Admin creates/selects a JD and tunes scoring weights, pass threshold and confidence cutoff.
3. **Résumé auto-scoring** — one structured `resume_match` LLM call per résumé → score 0–100, matched skills, gaps, summary, confidence.
4. **Promotion / archive** — `score ≥ threshold` → **Screening**; below → **Archived with reason**.
5. **Timed Q&A** — one question at a time (progress bar, per-question timer, auto-submit on timeout).
6. **Answer scoring** — one rubric-based `answer_score` LLM call per answer → score 0–5, justification, confidence, rubric hits.
7. **Fusion** — résumé + Q&A combined with JD-configured weights → **PASS / HOLD / REJECT**.
8. **Interview** — Admin assigns interviewer + date; interviewer reviews AI evidence and records a decision with timestamped notes.
9. **Audit** — every score, status transition and note is timestamped and viewable by Admin.

---

## A4. Frequently asked questions

**Q: What are the two AI prompts?**
`resume_match` (JD + résumé → score 0–100, matched skills, gaps, summary, confidence) and
`answer_score` (question + reference + answer + rubric → score 0–5, justification, confidence,
rubric hits). Both are single-turn, JSON-in/JSON-out. No agents, tools or multi-turn memory.

**Q: How does the LLM guardrail work?**
Every response is validated against a Pydantic schema. Invalid JSON → retry **exactly once** with
a correction instruction. Still invalid → controlled `LLMError` (no uncontrolled retry loops).

**Q: How is the combined score calculated?**
Q&A raw average (0–5) is normalized to 0–100 (`score / 5 × 100`), then combined with the résumé
score using the JD's weights (e.g. 60/40). `PASS` if `combined ≥ pass_threshold`; `REJECT` if
`combined < threshold − hold_margin` (default 15); otherwise `HOLD`.

**Q: What can the candidate see?**
Their live status, interview date, interviewer name, and after the Q&A their **aggregate combined
score, per-category breakdown and band**. AI justifications, rubric detail and raw prompts/evidence
are never exposed.

**Q: How are anti-cheat signals handled?**
Tab-switch, paste and copy-of-question events are captured client-side and sent with the
submission. They are surfaced to Admin/Interviewer as counters and (optionally) flags, and are
**never used for auto-reject**.

**Q: What is stubbed?**
Invitations — the Admin "Send invitation" action shows an in-app toast and writes an
`invitation.sent` audit event. No real email/SMS is sent.

**Q: Does it need an API key to run?**
No. The default `LLM_PROVIDER=mock` runs fully offline with deterministic heuristics. Set
`LLM_PROVIDER=openai`/`anthropic` and `LLM_API_KEY` for real model calls.

**Q: Where is data stored?**
In-memory SQLite, seeded from `input-data.json` at startup. State survives page refresh for the
session and resets on restart.

---

## A5. Seed dataset

**3 Job Descriptions:**

| JD | Role | Location | Exp | Weights (Résumé/QA) | Threshold |
|---|---|---|---|---|---|
| jd-1 | Frontend Developer | Mumbai | 2y | 0.6 / 0.4 | 70 |
| jd-2 | Java Backend Developer | Bengaluru | 3y | 0.6 / 0.4 | 72 |
| jd-3 | Python Developer | Pune | 2y | 0.5 / 0.5 | 70 |

**18 questions (6 per JD)** with reference answers and **rubric bands** (`score_5` / `score_3` /
`score_0`):
- *Frontend:* Virtual DOM, list virtualization, state management, JWT security, CSS box model, hook rules.
- *Java:* dependency injection, `@RestController`, JPA lifecycle, concurrency locking, exception handling, JWT + Spring Security.
- *Python:* collections, GIL, decorators, framework comparison, generators, SQLAlchemy transactions.

**10 synthetic résumés** covering edge cases:

| JD | Profiles |
|---|---|
| Frontend (4) | strong fit · missing TypeScript · senior overqualified · junior borderline |
| Java (3) | strong fit · legacy stack (no Spring Boot) · contradictory over-claim |
| Python (3) | strong fit · Django-only mismatch · data-science low-confidence |

**14 hard-coded logins** — 2 Admins, 10 Candidates, 2 Interviewers.

---

## A6. Definition of Done — success metrics

| Objective | Success metric (hackathon) | Status |
|---|---|---|
| End-to-end flow: JD → résumé scoring → screening → interview decision | Demonstrable walk-through with ≥ 2 JDs and candidates | ✅ 3 JDs, 10 candidates |
| Role-based UI (Admin / Candidate / Interviewer) | Each view reachable after login | ✅ |
| AI integration (2 structured prompts) | JSON output validated, retry on failure | ✅ |
| Data persistence (in-memory SQLite) | Actions survive page refresh for the session | ✅ |
| Auditability | Every score / status / note timestamped, viewable in Admin drill-down | ✅ |
| Anti-cheat telemetry (good-to-have) | Tab-switch, paste, copy-question counters captured and shown to Admin | ✅ |
| Score calculation | Score from résumé screening; if above threshold, trigger the test link and re-score on the test | ✅ |

---

## A7. In scope / out of scope

**In scope (must-have):** hard-coded users + JWT-style token; JD CRUD with configurable
weights/thresholds; résumé auto-scoring; above/below-threshold promotion & archive; timed rubric
Q&A; per-answer LLM scoring; weighted PASS/HOLD/REJECT; Admin dashboard with sort/filter,
drill-down, assign interviewer + date, "Next steps"; interviewer assigned-only UI; audit log;
pluggable LLM wrapper; local run via `uvicorn` + `npm run dev`.

**Out of scope (explicitly not built):** multi-turn or agentic AI; real email/SMS (stubbed toast
+ log only); PDF/DOCX parsing (résumés seeded as plain text); external queues/micro-services
(single monolith); production auth (OAuth/SSO); complex anti-cheat auto-reject decisions.

---

## A8. Task coverage

**Basic (must-have)** — ✅ project bootstrap (FastAPI + React + in-memory SQLite); ✅ seed JSON at
startup; ✅ REST CRUD for JDs/candidates/applications/status; ✅ role-based login; ✅ Admin
candidate list per JD sortable/filterable by status; ✅ candidate live status + interview date;
✅ interviewer assigned-candidate list + interview date.

**Intermediate (must-have)** — ✅ LLM client wrapper; ✅ `resume_match` strict JSON; ✅ auto-promotion
/ archive with reason; ✅ Q&A UI (one question, progress, timer, auto-submit); ✅ `answer_score`
strict JSON; ✅ weighted combined + band (candidate sees aggregate + band, no justification);
✅ Admin drill-down (evidence, answers, scores, confidence, timings); ✅ assign interviewer + date;
✅ interviewer status toggle + timestamped notes; ✅ candidate sees interviewer name; ✅ sortable
/ filterable ranked shortlist.

**Advanced (good-to-have)** — ✅ anti-cheat telemetry (tab-switch, paste, copy-of-question) surfaced
to Admin, never auto-reject; ✅ auto-flag on low confidence / score disagreement; ✅ "Next Steps"
log per candidate; ✅ stubbed invitation (toast + audit event); ✅ retry-on-invalid-JSON once +
schema validation; ✅ configurable per-JD weights/threshold/cutoff from the Admin UI; ✅ Admin can
review LLM evidence before the final call; ✅ Docker (Compose) for local demo. ⏳ Logging/alerts
for error tracing are minimal.

---

## A9. Guardrails (what NOT to do)

- Never call the LLM in a loop without the JSON-schema guard rail — retry at most once.
- Do not expose AI justifications or raw prompts to the Candidate view.
- Do not store API keys in source control — use `.env`.
- Do not implement real email/SMS — only stubbed toast notifications.
- Do not add external services (Kafka, S3, etc.) — keep everything in the single repo/container.
- Do not write production-grade authentication — hard-coded users only.

---

## A10. Expected outcomes

- **AI-driven shortlisting** — every résumé auto-scored against the JD; qualified candidates
  surfaced in minutes, unqualified archived with a reason.
- **Consistent conceptual screening** — rubric-based AI scoring of free-text answers gives every
  candidate the same yardstick with justification and confidence.
- **One combined decision signal** — résumé-match and Q&A fused into a single PASS/HOLD/REJECT
  band with full evidence.
- **Role-based clarity** — Admin runs the pipeline, Interviewer sees only assigned candidates,
  Candidate sees only their status; no email, no confusion.
- **Live, auditable status** — every candidate's stage is visible on the Admin dashboard,
  drillable to AI scores, notes and anti-cheat flags.
- **Faster, fairer hiring** — time-to-shortlist cut from days to minutes; decisions backed by
  explainable, reproducible AI evidence.

---

## A11. Known limitations / demo notes

- The offline **mock** provider uses deterministic keyword/overlap heuristics, so it cannot detect
  a *contradictory over-claim* résumé (e.g. exaggerated experience). Configure a real
  `LLM_PROVIDER` for semantic judgment.
- **Screening trigger** is on-demand per JD from the Admin (not a background daemon at intervals).
- **Docker** runs backend + frontend as two Compose services (single-container is optional in the spec).
- **Candidate score visibility:** the spec contains a contradiction (aggregate score vs.
  final status only); this implementation shows the aggregate score, per-category breakdown and
  band, while hiding AI justifications and raw evidence.

---

## B0. How to use this guide

- **Per intern:** pick a **different question mix** every time so they can't pre-share answers.
  Use the ready-made **Tracks A–E** in §B15 (each track = 12 questions + 1 coding task + 1 review
  task) or build your own from the bank.
- **Time budget:** ~45–60 min per intern. 5 min project walk-through, 25 min Q&A bank,
  15 min live coding, 10 min code review, 5 min wrap-up.
- **Difficulty:** 🟢 foundation · 🟡 working knowledge · 🔴 senior / stretch.
- **Format per question:** *Q* → *Look for* (model answer) → *Follow-up* (probe deeper) →
  *Red flags* → *Anchor* (where it lives in the repo).
- **Scoring:** use the scorecard in §B16. Weight *reasoning* over recitation; reward candidates
  who admit uncertainty and reason from first principles.
- **The strongest signal:** can they connect a design choice to a *trade-off* and name what they
  gave up?

> Tip: always open the intern's actual file (`Anchor`) and ask them to talk to their own code.
> Their memory of the code is a signal in itself.

---

## B1. Orientation & project comprehension

**Q1 🟢** Walk me through the system end to end in 90 seconds.
*Look for:* seed at startup → login/roles → Admin runs résumé screening (`resume_match`) →
promotion/archive by threshold → candidate timed Q&A (`answer_score`) → weighted fusion →
PASS/HOLD/REJECT → interviewer assignment & decision → audit.
*Follow-up:* Where does the "human in the loop" safety sit?
*Red flags:* describes it as fully automated hiring; can't name the two prompts.
*Anchor:* `backend/main.py`, `backend/services/`

**Q2 🟢** Why two LLM prompts and not five? What breaks if you add more?
*Look for:* single responsibility per prompt; deterministic/explainable scoring; cost/latency and
testability; multi-turn rejected on purpose.
*Follow-up:* Which prompt is riskier to change and why?
*Red flags:* "more prompts = smarter".
*Anchor:* `backend/ai/`

**Q3 🟡** What is the "single source of truth" in this app and what makes it truthful?
*Look for:* `Application` row holds status/band/scores; audit log timestamps transitions;
evidence (`resume_evidence`, answers) is persisted, not recomputed on read.
*Red flags:* says "the frontend state".

**Q4 🟡** If I refresh the browser mid-session, what survives and what doesn't? Why?
*Look for:* DB is in-memory but the **process** keeps it; refresh only re-loads the SPA, so data
survives; a **server restart** wipes it and re-seeds.
*Follow-up:* What about running `uvicorn --workers 4`?
*Red flags:* "data is lost on refresh".
*Anchor:* `backend/database.py`, README.

**Q5 🔴** `uvicorn --workers 4` is turned on in production. What goes wrong here specifically?
*Look for:* in-memory SQLite per process → four disjoint databases; StaticPool is per-process;
logins/data inconsistent across requests; audit split. Real fix: persistent DB or single worker.
*Award:* top marks for spotting the per-process isolation.
*Anchor:* `backend/database.py`.

---

## B2. Architecture & module boundaries

**Q6 🟡** Why the layering `api → services → repositories → models`? What leaks if you skip `services`?
*Look for:* routers stay thin/HTTP-only; business rules testable without HTTP; repositories hide
SQL. Skipping services puts business logic in controllers → untestable, duplicated.
*Follow-up:* Point at a rule that would be tempting to put in a router.

**Q7 🟡** `schemas/` vs `models/` — why two copies of "the same" object?
*Look for:* ORM entities (persistence) vs Pydantic DTOs (API contract) with different lifecycles;
never expose ORM directly; input vs output schemas differ (e.g. `QuestionPublic`).
*Red flags:* "they're the same thing".

**Q8 🟡** `serializers.py` builds DTOs by hand. What are the trade-offs vs `from_attributes`/`model_validate`?
*Look for:* hand-built supports computed/joined fields (`candidate_name`, `telemetry`, derived
`interviewer_name`); cost is boilerplate + drift risk. `from_attributes` is terse but can't join.
*Follow-up:* How would you prevent drift as fields grow?

**Q9 🔴** The repositories are very thin. Is that layering pulling its weight, or is it ceremony?
*Look for:* a genuine opinion either way with a reason — thin repos centralize queries and ease
swapping/mocking; ceremony if they only forward `db.get`. Reward nuanced answers over dogma.
*Red flags:* recites "always use repository pattern" with no trade-off.

**Q10 🟡** Where would you add a "notification" feature touching email + in-app? Which layer?
*Look for:* a `services/notification` + an interface/port; routers just call it; provider swappable
(like the LLM client). Not in the router, not in the ORM.

---

## B3. Data model & persistence (SQLAlchemy / SQLite)

**Q11 🟢** Name the 7 core entities and the join table at the center. Why is it central?
*Look for:* JobDescription, Candidate, Question, Application, Answer, Interview + User; `Application`
is the join holding scores/band/status. (Also AuditLog, Flag, TelemetryEvent.)

**Q12 🔴** The seed file uses string ids (`jd-1`, `cand-1`); the DB uses integer PKs. How did you
reconcile, and what could go wrong?
*Look for:* seed builds `{external_id: row}` maps and cross-references candidates/JDs/questions;
loses the original id unless stored (`external_id`); risk of dangling refs if an id is missing.
*Follow-up:* How would you make it robust to a bad row? (skip + report vs crash).
*Anchor:* `backend/seed.py`.

**Q13 🔴 (tricky)** In `screening_service`, evidence is built as a dict, then later
`application.resume_evidence["archive_reason"] = ...` is set *in place*. What can silently break?
```python
application.resume_evidence = {"matched_skills": ..., "gaps": ..., "summary": ...}
self.db.flush()
...
application.resume_evidence["archive_reason"] = "..."   # in-place mutation
```
*Look for:* SQLAlchemy's JSON column doesn't track in-place mutation of a plain `dict`; the change
may not be persisted unless you reassign (`application.resume_evidence = {**d, ...}`) or use
`MutableDict`. This is a real, subtle bug class.
*Follow-up:* Two fixes? (reassign; `MutableDict.as_mutable(JSON)`).
*Award:* top marks for this one.

**Q14 🟡** `weights` is a JSON column holding `{resume: 60, qa: 40}`. Why JSON and not two float columns?
*Look for:* flexible/evolvable config; trade-off: weaker typing/validation, harder to query,
can drift (must validate sums in the service). Either column choice is defensible if reasoned.

**Q15 🔴** Enumerate the relationships and their cardinalities. Which one is `one-to-zero-or-one` and why?
*Look for:* JD→Questions/Candidates/Applications (1:N), Candidate→Applications (1:N),
Application→Answers (1:N), Question→Answers (1:N), Application→Interview (`1:0..1`, created on
assignment), Application→AuditLog/Flags (1:N).
*Red flags:* can't justify the 0..1.

**Q16 🟡** Why `poolclass=StaticPool` and `check_same_thread=False` for the in-memory SQLite?
*Look for:* a single shared connection so the in-memory DB isn't recreated per connection; disabling
the thread check lets FastAPI's threadpool use it. Cost: serialized access / limited concurrency.
*Follow-up:* What replaces this with a real DB?

**Q17 🔴** The audit log is append-only by convention. What would you add to enforce it?
*Look for:* DB perms/no UPDATE/DELETE, insert-only repo, hash-chaining for tamper evidence,
monotonic timestamps, retention policy.

---

## B4. AuthN / AuthZ & security

**Q18 🟢** How does a request get from "logged in" to "allowed"? Trace it.
*Look for:* `POST /login` → signed JWT → frontend stores it → `Authorization: Bearer` →
`get_current_user` (`bearer_scheme`) → `require_role(...)` on the route.

**Q19 🔴** Passwords are hashed with a bare `sha256` and compared with `==`. Why is that not
acceptable, and what would you do?
*Look for:* no salt → rainbow tables, identical passwords collide; SHA-256 is fast → GPU brute
force; `==` is not constant-time → timing oracle. Fix: bcrypt/argon2/scrypt + `hmac.compare_digest`.
*Follow-up:* Would you ever "encrypt" instead of hash? (No — hashing is one-way.)
*Award:* top marks for the timing-attack point.
*Anchor:* `backend/auth/security.py`.

**Q20 🔴** The frontend stores the JWT in `localStorage`. Threat model?
*Look for:* XSS steals the token; any injected script/third-party dep reads it. Mitigations:
httpOnly cookie (+CSRF), short-lived access token + refresh, CSP, avoid `dangerouslySetInnerHTML`.
*Red flags:* "localStorage is secure because it's not a cookie".

**Q21 🟡** `allow_origins=["*"]` together with `allow_credentials=True` — problem?
*Look for:* browsers reject `*` with credentials, and it's overly permissive; enumerate origins.
*Anchor:* `backend/main.py`.

**Q22 🔴** A candidate calls `GET /applications/{id}` for someone else's application. Walk the
authorization and name the failure modes if it were wrong.
*Look for:* `_authorize_view` allows admin, owner (candidate.user_id), or assigned interviewer;
else 403. Failure modes: IDOR, data leak of evidence, cross-tenant access. Authorization must be
server-side, not by hiding routes.
*Anchor:* `backend/api/applications.py`.

**Q23 🟡** Why is "hidden frontend routes are not security" a recurring rule here?
*Look for:* client is untrusted; anyone can call the API; enforce on the server. The SPA's
`ProtectedRoute` is UX only.

**Q24 🔴** Login has no rate limiting. Describe an attack and two defenses.
*Look for:* credential stuffing/brute force on hard-coded users; per-IP/user throttle, lockout,
CAPTCHA, exponential backoff, logging/alerting; also don't reveal which factor failed.

---

## B5. AI / LLM integration & guardrails

**Q25 🟢** What does `complete_json` guarantee? List the steps.
*Look for:* calls provider → strips code fences/prose → `json.loads` → `schema.model_validate` →
on failure retry **once** with a correction instruction → else raise `LLMError`.
*Anchor:* `backend/ai/llm_client.py`.

**Q26 🔴 (tricky)** The retry policy is "exactly once". When is retrying *wrong*? Hints: billing,
latency, determinism, duplicate side effects.
*Look for:* retry multiplies cost; can double-charge; non-idempotent side effects; latency budget
(2–3s target); may mask a systematically bad prompt; "retry once" is a policy, not a fix for a
bad schema. Also: retrying a *timeout* is different from retrying *invalid JSON*.

**Q27 🔴** Why validate the LLM output against a Pydantic schema at all — isn't the prompt enough?
*Look for:* models drift/hallucinate; prompts aren't contracts; ranges (`0..100`, `0..1`) and
types must be enforced; protects the DB and downstream math; fail closed, not silently.
*Follow-up:* What happens to a score of `150`? (`ValidationError` → retry → `LLMError`).
*Anchor:* `backend/schemas/llm.py`.

**Q28 🟡** How would you swap OpenAI for Anthropic without touching business logic? Show the seam.
*Look for:* `Provider` protocol + `build_client()` factory reading `LLM_PROVIDER`; services depend
on `LLMClient`, not the vendor. Dependency inversion.
*Anchor:* `backend/ai/llm_client.py`.

**Q29 🔴 (tricky)** `_strip_code_fences` also extracts the first `{...}` from prose using
`find("{")`/`rfind("}")`. When does that heuristic produce a *wrong-but-valid* JSON object?
*Look for:* multiple JSON objects, braces inside strings, nested prose examples, markdown with two
code blocks → picks outermost span and may merge; silently accepts the wrong object instead of
failing. Better: strict parse, or a single enforced JSON object, or a JSON-mode/function-calling API.

**Q30 🔴** The mock provider uses keyword/stem overlap. Give two ways it produces misleading scores.
*Look for:* negation/context blindness ("no production Airflow" — mitigated by weak-signal
heuristics but still brittle); synonyms ("Postgres" vs "PostgreSQL"); stemming collisions;
scores float work like "React" in every frontend résumé → no discrimination. Lesson: heuristics
are a stand-in, not a substitute for semantic judgment.
*Anchor:* `backend/ai/resume_match.py`, `answer_score.py`.

**Q31 🔴 (tricky)** `answer_score` heuristic only counts `score_5` band hits for the numeric score;
`score_3` items are collected but never raised the score. Is that a bug? Defend either way.
*Look for:* awareness that it's a simplification; a defensible model (partial credit should move
the score); or an argued equivalent. Top marks for proposing `score = 5·(hits5/|5|) + 3·(hits3/|3|)`
normalized, or similar.

**Q32 🟡** Why does the candidate endpoint never return `reference_answer`, `rubric_hits` or
`justification`? Where is that enforced?
*Look for:* least privilege / anti-gaming; `QuestionPublic` DTO omits them; application detail is
viewed by candidate but justification is not in the candidate-facing contract for answers they see.
*Follow-up:* Is hiding it in the DTO enough, or should it also be checked by role? (Both.)

---

## B6. Scoring, business rules & math

**Q33 🟡** Derive the combined score formula. Where are weights normalized and why normalize?
*Look for:* `combined = w_resume·resume + w_qa·qa`, weights normalized to sum 1 so 60/40 or 0.6/0.4
both work and misconfigs don't distort; `normalize_qa = avg/5×100`.
*Anchor:* `backend/services/scoring_service.py`.

**Q34 🔴 (tricky)** What is `combined_score` when Q&A hasn't happened (`qa_score is None`)?
What are the consequences?
```python
combined = w["resume"] * (resume_score or 0) + w["qa"] * (qa_score or 0)
```
*Look for:* `None` becomes `0`, so a résumé-only candidate is scored *down* as if they failed the
test — mathematically "fine" but semantically wrong; fusion should arguably be gated on both
parts or use "not yet scored" until Q&A completes. Great answer if they spot the `or 0` trap.

**Q35 🔴** Boundary semantics: `PASS if combined >= threshold`; `REJECT if combined < threshold − margin`;
else HOLD. What's the exact HOLD band? Is the margin inclusive? What would you test?
*Look for:* `[threshold − margin, threshold)` is HOLD; boundaries: `70→PASS`, `69.99→HOLD`,
`55→HOLD`, `54.99→REJECT` (with margin 15). Tests already encode this.
*Anchor:* `backend/tests/test_scoring.py`.

**Q36 🟡** Why persist the résumé score **before** changing status?
*Look for:* partial-failure safety — if the LLM/next step fails or the process dies, the successful
score isn't lost and status isn't advanced on unverified data; auditability.
*Anchor:* `backend/services/screening_service.py`.

**Q37 🔴** Thresholds/weights are per JD. Name two ways a misconfiguration could hurt, and how you'd
defend.
*Look for:* weights summing to 0/negative → division/garbage; threshold out of range; too-low
threshold floods screening. Defenses: validation at the API boundary (already `_validate_config`),
UI constraints, tests, sane defaults.

**Q38 🟡** A candidate times out with an empty answer. What score/confidence should that get, and why?
*Look for:* 0 score, high confidence in "no answer" (currently implemented); discuss whether
timeout should be neutral, penalized, or flagged. Reasoning matters more than the choice.

**Q39 🔴** "AI performs structured assessments; humans retain the final decision." Where does the
code enforce *not* auto-rejecting?
*Look for:* flags are advisory; decisions require an interviewer; screening archives below-threshold
but never "rejects" a person; no auto-reject path in anti-cheat; candidate sees band, not verdict.

---

## B7. REST API & backend design

**Q40 🟢** What does `POST /applications/{id}/answers` do, step by step?
*Look for:* auth owner → validate question belongs to JD → `answer_score` → upsert Answer →
store telemetry → if all answered, finalize fusion → audit → return sanitized `AnswerOut`.

**Q41 🟡** Why 401 vs 403 vs 422 semantics? Give an example of each in this app.
*Look for:* 401 no/invalid token; 403 authenticated but not allowed (candidate reading others);
422 validation (bad decision value). Bonus: 404 for missing resources.

**Q42 🔴** The API returns DTOs, not ORM objects. Where could an ORM object leak PII or internals?
*Look for:* lazy-loaded relationships in serializers causing N+1 and accidental exposure; adding
`model_config = from_attributes` too broadly; `Answer` containing `justification` returned to
candidates if the wrong schema is used.

**Q43 🔴 (tricky)** `GET /applications` lists everything, then Python filters/sorts. Where does this
break at scale, and what's the fix?
*Look for:* O(n) loads + N+1 for `candidate`/`jd`; pagination + filtered SQL + joins/`selectinload`;
indexes; DTO built from a projection. Also note the dashboard "recent" is just the last by id, not
by timestamp.
*Anchor:* `backend/repositories/repository.py`, `serializers.py`.

**Q44 🟡** `GET /applications/mine` vs `GET /applications` — why split them?
*Look for:* least privilege; a candidate shouldn't be able to list all applications; the shape and
authorization differ. Hiding on the client is not enough.

**Q45 🔴** Design the "bulk screening across all JDs on a schedule" feature (the spec's batch idea).
*Look for:* a job runner (in-process scheduler like APScheduler, or separate worker), idempotency
(per candidate/JD key), locking to avoid double-run, progress model + polling endpoint, retries with
backoff, and *not* blocking an HTTP request. Note the tension with "no external queue".

---

## B8. Frontend / React / UX

**Q46 🟢** How does the SPA know which portal to render? Trace auth → routing.
*Look for:* `AuthContext` (`me()` on load) → `ProtectedRoute role=...` → role-specific layout/nav;
token in `api` client; `homeFor(role)`.

**Q47 🔴 (tricky)** `React.StrictMode` double-invokes effects in dev. What could that do to this
Q&A screen (timers, telemetry, submissions)?
*Look for:* double-mounted effects → duplicated listeners → double-counted tab-switch/paste;
interval started twice; potential double-submit if not guarded by the `submitted` ref. Discussion of
cleanup functions and idempotent submit.
*Anchor:* `frontend/src/pages/Candidate/QAScreening.jsx`.

**Q48 🔴** The Q&A `submit` is a `useCallback` with several deps, and the timer calls it on `0`.
Point out a stale-closure or race risk and how you'd harden it.
*Look for:* `seconds` effect capturing `current`/`text`; `submitted` ref prevents double submit;
reset of `submitted` on question change; risk if `text` changes after timeout; consider a state
machine (`idle|answering|submitting`).

**Q49 🟡** The candidate list sorts/filters in memory with `useMemo`. When is that the wrong choice?
*Look for:* large datasets → do it server-side with pagination; in-memory is fine for a demo.
*Follow-up:* What would the API contract look like for server-side sort/filter?

**Q50 🟡** Why is the JD rubric editor three comma-separated inputs (score_5/3/0) and what's wrong
with that UX?
*Look for:* matches the data model; problems: comma-in-text ambiguity, no structure, error-prone;
better: repeatable chips/rows or a JSON editor with validation.
*Anchor:* `frontend/src/pages/Admin/JDEditor.jsx`.

**Q51 🟢** What's wrong with using array index as a React key? Where might that bite here?
*Look for:* reordering/insertion breaks identity/state; use stable ids (`q.id`). In the JD editor
questions list, index keys can misbehave when removing a row.

**Q52 🟡** How would you make the Q&A screen accessible (a11y) and mobile-friendly?
*Look for:* labels/aria-live for the timer, focus management, keyboard flow, 44px targets,
`prefers-reduced-motion`, color contrast, no reliance on color alone for PASS/HOLD/REJECT.

---

## B9. Concurrency, performance & correctness

**Q53 🔴** `_finalize_if_complete` runs on the last answer. Two rapid duplicate submits of the last
answer arrive concurrently. What happens?
*Look for:* possible double finalize / race; answers upsert by (application,question) helps but
finalize isn't locked; recommend a status guard ("only finalize if not already finalized"), a DB
unique constraint, or a transaction with row lock. Note SQLite's coarse locking.

**Q54 🔴** Is `verify_password` comparison constant-time? Why should it be?
*Look for:* no; `==` short-circuits → timing leak. Use `hmac.compare_digest`. (Cross-ref Q19.)

**Q55 🟡** Where are the N+1 query risks in this codebase?
*Look for:* listing applications and touching `.candidate`/`.jd` per row; `interviews_for_interviewer`
→ `interview.application`; `jd.questions` length in `jd_dto`. Fix with eager loading or joins.

**Q56 🟡** The app targets "LLM response in 2–3 seconds". How would you meet that for a *batch* of 50
résumés without freezing the request?
*Look for:* concurrency (bounded `asyncio.gather`/thread pool), per-item progress, background task +
poll, timeouts, caching, and cost limits; never N sequential blocking calls in one request.

**Q57 🔴** Timestamps: `utcnow()` returns timezone-aware UTC; some inputs (datetime-local) are naive.
Where could a naive/aware comparison raise or silently mis-schedule?
*Look for:* mixing naive and aware in comparisons/subtraction; storing naive; `Z` parsing; recommend
store-UTC-aware, convert at the edges.

---

## B10. Error handling & observability

**Q58 🔴 (tricky)** In `qa_service.submit_answer`, `scorer.score(...)` can raise `LLMError`, but
this path isn't wrapped like `screening_service` is. What does the candidate experience, and what
should happen?
*Look for:* an unhandled `LLMError` → 500 / opaque failure mid-test; should map to a controlled
error (e.g. 502/503 with a retry affordance), preserve the answer draft, and never lose the
question order. Contrast with screening which catches per-candidate and continues.

**Q59 🟡** What is the difference between a `4xx` and `5xx` here, and why does it matter to the client?
*Look for:* 4xx = caller's fault (fix the request, don't retry blindly); 5xx = server's fault
(transient, retry with backoff). The frontend should treat them differently.

**Q60 🟡** The spec mentions "logging and alerts". What would you log for the LLM path, and what
must you *never* log?
*Look for:* log latency, provider, model, retry count, error class, correlation id; never log API
keys, full prompts with PII, or raw résumé text; redact and sample.

**Q61 🔴** How would you surface partial failures of a batch screening run to the admin?
*Look for:* per-item result with error, aggregate counts (scored/promoted/archived/errors), a
retry-failed action, and an audit event per error — matching `ScreeningResult`.

---

## B11. Testing & quality

**Q62 🟢** What's the difference between unit and integration tests here? Give one of each.
*Look for:* unit = `scoring_service`/heuristics; integration = `TestClient` hitting `/login` →
screening → Q&A with a fresh seeded DB per test.

**Q63 🟡** Why does the LLM test use an injected `CallableProvider` instead of the real API?
*Look for:* deterministic, fast, offline, no cost/key; you can force malformed JSON to test the
retry-then-fail path. This is dependency injection + test doubles.

**Q64 🔴** Write the assertions you'd add for the "exactly one retry" rule.
*Look for:* count provider calls == 2; first call invalid, second valid → returns; both invalid →
raises `LLMError`; *no* third call. Already exists — ask them to explain their own test.

**Q65 🔴** The tests `drop_all/create_all` per test with a shared engine. What are the risks and why
does it work here?
*Look for:* state bleed between tests if not reset; StaticPool shared connection; order independence;
parallel test execution would break it. Good discussion of test isolation.

**Q66 🟡** Name three things that are currently *untested* that you'd cover next.
*Look for:* concurrent finalize, in-place JSON mutation, interviewer decision state machine,
telemetry flag thresholds, pagination, auth token expiry/revocation.

**Q67 🔴 (tricky)** How would you test that a candidate can *never* see another candidate's data,
including through indirect responses (errors, counts, timing)?
*Look for:* property/matrix tests across every candidate endpoint for every other application id;
assert 403 and no field leakage; avoid existence oracles (consistent 404/403); include `mine`,
questions, answers, telemetry.

---

## B12. Git, DevOps & deployment

**Q68 🟡** What is in `.gitignore`, and why must `.env` never be committed while `.env.example` should be?
*Look for:* `.env` may hold secrets (API key, JWT secret); `.env.example` documents required vars
with no secrets.

**Q69 🔴** Walk the Docker Compose topology and where requests flow.
*Look for:* nginx serves the built SPA and proxies `/api/` to `backend:8000`; backend seeds on
startup; two services; env passed via compose. Trade-offs vs a single container.

**Q70 🟡** Why is the in-memory DB a problem for a "real" deploy and what's the migration path?
*Look for:* data loss on restart, per-process isolation, no durability; move to Postgres/MySQL,
add migrations (Alembic), connection pooling, and stop bundling state with the app.

**Q71 🔴** If the LLM provider is down during a demo, what's your fallback and why is that safe?
*Look for:* `LLM_PROVIDER=mock` deterministic fallback; the interface makes it swappable; but note
it changes scoring semantics — decide consciously and document it.

---

## B13. Software-engineering principles (apply to *their* code)

**Q72 🟡** Point to a place that follows SRP and a place that's at risk of violating it.
*Look for:* `llm_client` (transport+validation) vs `screening_service` (orchestration+persistence+
audit). If they flag `screening_service` doing too much, that's a strong answer.

**Q73 🔴** Find a spot that violates DRY. Is the duplication *harmful* or acceptable?
*Look for:* serializer field repetition; `_append_note`; flag `add_flag` dedup. Reward "duplication
is cheaper than the wrong abstraction" — not blanket DRY.

**Q74 🟡** Where did you apply YAGNI, and where did you over-engineer?
*Look for:* honest self-assessment. E.g. repositories may be ceremony; `Flag`/`TelemetryEvent`
tables justified by features; a `Flag` dedupe by "signature" may be premature.

**Q75 🔴** Coupling vs cohesion: which module has the highest fan-out, and is that a problem?
*Look for:* services importing many peers (flags, scoring, audit, repositories) — acceptable for
orchestration but hard to test; suggest ports/interfaces or events to decouple side-effects.

**Q76 🔴** Give an example of a *leaky abstraction* in the codebase.
*Look for:* DTOs that mirror ORM exactly; `_as_percent` guessing fractions vs percentages; the
`weights` JSON leaking into the service math; frontend knowing the exact status vocabulary.

**Q77 🟡** Composition vs inheritance in this codebase: where and why did you choose one?
*Look for:* provider protocol + composition of `LLMClient`; relationships not deep class
hierarchies. Nothing needs inheritance here — good.

**Q78 🔴** If you had 4 more hours, what's the single highest-risk thing you'd fix and why?
*Look for:* prioritization tied to risk (e.g. non-constant-time password compare, in-place JSON
bug, candidate answer 500 on LLM failure, JWT in localStorage). Any answer that names a *real*
risk with impact beats a feature wishlist.

---

## B14. Tricky / rapid-fire (good for quick discrimination)

| # | Question | One-line expected |
|---|---|---|
| R1 | `None or 0` — value? | `0` |
| R2 | `list.sort()` return value? | `None` (in-place) — the code avoids it with `.map` copy |
| R3 | `default=dict` vs `default={}` in SQLAlchemy? | callable avoids shared mutable default |
| R4 | Why `{**d, "k": v}` instead of `d["k"]=v` for JSON columns? | forces change tracking |
| R5 | `HTTPBearer(auto_error=False)` — why? | return 401 ourselves, not `403`/redirect |
| R6 | 422 vs 400 here? | Pydantic/FastAPI validation is 422; semantic bad request is 400 |
| R7 | Why `select(func.count())`? | SQL `COUNT(*)`, not loading rows |
| R8 | `check_same_thread=False` risk? | true cross-thread sharing → guard with pooling |
| R9 | JWT `exp` claim purpose? | server-side expiry check on decode |
| R10 | Why is `sanitize/escape` relevant to a JWT-in-localStorage decision? | XSS is the theft vector |
| R11 | Why `functools.wraps` in decorators (if they used any)? | preserve `__name__`/`__doc__` |
| R12 | What is an IDOR and where could it occur? | predictable ids + missing authz; `/applications/{id}` |
| R13 | TCP vs HTTP vs REST — clarify the stack? | REST is an architectural style over HTTP over TCP |
| R14 | Idempotent endpoints here? | `GET`s, and ideally `PUT`; `POST /answers` is an upsert (idempotent-ish) |
| R15 | Time complexity of in-memory sort/filter of candidates? | `O(n log n)` + `O(n)` |
| R16 | Why normalize weights before combining? | scale invariance / avoid 0 division |
| R17 | What does `model_validate` raise on bad data? | `ValidationError` |
| R18 | Difference: `flush()` vs `commit()`? | `flush` writes SQL; `commit` ends the tx |
| R19 | What's a transaction boundary in this app? | per-request session; commits at service end |
| R20 | Why return `202` for telemetry? | accepted/async-ish, no body needed |
| R21 | Why not store the raw prompt? | PII/cost and leakage into candidate-visible data |
| R22 | `find("{")`/`rfind("}")` failure mode? | merges multiple objects / picks wrong span |
| R23 | Where's the SSRF/secret risk if "provider base URL" is user-controlled? | key to attacker URL |
| R24 | Why an `evals/`-style golden set for prompts? | regression-test AI quality, not just JSON validity |
| R25 | Why is "AI 90% accurate" not enough for hiring? | fairness/bias/audit; humans decide; explainability required |

---

## B15. Pre-built tracks (give each intern a different one)

Each track: **6 conceptual + 4 deep + 2 tricky + 1 live-coding + 1 code-review** — mix and match so
no two interns get the same set. Rotate the coding/review tasks and swap in fresh numbers from §B13–B14.

| Track | Conceptual | Deep | Tricky | Coding task | Code review |
|---|---|---|---|---|---|
| **A** | Q1, Q2, Q6, Q18, Q33, Q40 | Q13, Q43, Q53, Q58 | Q29, Q38 | T1 | CR1 |
| **B** | Q3, Q7, Q11, Q25, Q34, Q46 | Q19, Q30, Q56, Q65 | Q28, Q41 | T2 | CR2 |
| **C** | Q4, Q8, Q20, Q26, Q36, Q48 | Q16, Q37, Q55, Q60 | Q31, Q44 | T3 | CR3 |
| **D** | Q5, Q9, Q12, Q21, Q39, Q50 | Q23, Q27, Q51, Q67 | Q33, Q57 | T4 | CR1 |
| **E** | Q10, Q15, Q22, Q35, Q47, Q61 | Q24, Q32, Q62, Q69 | Q17, Q45 | T2 | CR3 |

### Live-coding tasks
- **T1** Add a new JD field (`employment_type`) through model → schema → seed → service → API → UI, with validation.
- **T2** Extend `/applications` with pagination + `?status=` and `?jd_id=` filters (server-side), plus a test.
- **T3** Add a unit test proving the exact HOLD-band boundaries; then make one boundary deliberately off-by-one and show the test catches it.
- **T4** Add a new LLM provider (e.g. a fake "echo" provider) via the factory, and a test that it is selected by `LLM_PROVIDER`.

### Code-review tasks (hand them the snippet, ask for issues)
- **CR1** The in-place JSON mutation from **Q13**. Ask: is it persisted? why/why not? fix it.
- **CR2** The `qa_service.submit_answer` path from **Q58**. Ask: what happens on `LLMError`? improve it.
- **CR3** `verify_password` from **Q19**. Ask: two security problems and the fix.

---

## B16. Scorecard

Score each dimension **1–5** (1 = absent, 3 = working knowledge, 5 = deep + trade-offs). Weight as shown.

| Dimension | Weight | 1–5 | Notes |
|---|---|---|---|
| Code comprehension (their own code) | 15% | | |
| Architecture & boundaries | 10% | | |
| Data modeling / SQL | 10% | | |
| Security awareness | 15% | | |
| AI/LLM rigor & guardrails | 15% | | |
| Testing & correctness | 10% | | |
| Debugging under pressure | 10% | | |
| Communication & honesty about gaps | 5% | | |
| Engineering principles (SRP/DRY/trade-offs) | 5% | | |
| Live-coding execution | 5% | | |

**Weighted total:** ______ / 5

**Calibration bands**
- **4.3–5.0** Hire-ready: reasons from first principles, names trade-offs, finds the tricky bugs.
- **3.5–4.2** Strong: solid understanding, some depth on their own code, minor gaps.
- **2.5–3.4** Developing: can explain the what, weak on the why; needs guidance.
- **< 2.5** Needs fundamentals: recites without understanding; cannot reason about their own code.

**Mandatory red flags (any one caps the score at 2.0 regardless of the rest):**
- Claims security is "handled" while passwords are unsalted and tokens are in localStorage.
- Cannot explain why the LLM output is schema-validated.
- Says the app auto-rejects candidates or that AI makes the final hiring decision.
- Copied code they cannot explain.

---

## B17. Interviewer tips

- Ask **"why", then "what did you give up?"** on every design answer.
- When they're stuck, downgrade to a hint, not the answer — measure how they recover.
- Prefer **their** code as the substrate; make them navigate it live.
- Reward **"I don't know, but here's how I'd find out"** over confident wrong answers.
- End with: *"What's the weakest part of your implementation, and how would you fix it?"* — the
  answer separates the top tier more than any other question.
