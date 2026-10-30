# Graveyard of Dead Software: MVP & Workflow

> A digital cemetery for software the internet forgot. An agent exhumes a dead
> service from the Wayback Machine, determines cause of death from evidence,
> writes a eulogy with open-weight Gemma, and fact-checks itself before burial.

Deadline: Oct 31, 2026 (Hacktoberfest DEV Challenge Week 4, "Ghost in the Machine")
Target categories: Overall · Gemma ($200) · Render ($200) · Browserbase ($100, deep) · Sentry ($100) · .tech ($100, optional)

---

## 1. MVP definition (what "done" means)

The MVP ships when ALL of these are true:

- [ ] 15 seed graves contain REAL data: CDX lifeline, ≥3 exhumed snapshots,
      ≥1 screenshot, Coroner verdict with evidence IDs, Gemma eulogy, claims list,
      unsupported_before / unsupported_after counts.
- [ ] One live /bury by a stranger completes end-to-end in < 3 min on Render.
- [ ] /benchmark shows ≥ 30 exhume attempts comparing Browserbase vs HTTP.
- [ ] Sentry shows full traces for ≥ 15 digs (agent → chat → tool spans, tokens, latency).
- [ ] Every grave page shows "Eulogy written by <model>" and links its sources.
- [ ] Site is live on Render (+ .tech domain if claimed).
- [ ] DEV post published with metrics tables, screenshots, Sentry traces, demo GIF.

Out of scope for MVP: accounts, editing graves, séance chat (stretch), RL, mobile polish beyond basic responsive.

---

## 2. Architecture

FastAPI + Jinja2 + SQLite · background job runner · Sentry · Render

```
POST /bury ──► jobs table ──► worker runs 5 stages, each persisted & resumable
                                   │
  1 Archaeologist  CDX API → lifeline, birth/peak/last-alive/post-death snapshots
  2 Exhumer        Browserbase (Stagehand extract + screenshot) → HTTP id_ fallback
  3 Coroner        deterministic signals + Gemma → cause enum, time of death, [E#] cites
  4 Eulogist       Gemma → epitaph, eulogy, survived_by (must cite [E#])
  5 Fact-checker   claims → verify vs evidence → rewrite once → before/after counts
                                   │
                         grave row status=done ──► /grave/<slug>
```

### Routes
| Route | Purpose |
|---|---|
| `GET /` | Cemetery grid + stats bar |
| `GET /grave/<slug>` | Lifeline, cause, sources, claims, attempts, memories, model credit |
| `POST /bury` | 3/hour/IP, returns job id |
| `GET /job/<id>` | Poll: stage, status, error |
| `POST /marigold/<slug>` | Rate limited |
| `POST /memory/<slug>` | Rate limited, length-capped, basic profanity/URL filter |
| `GET /benchmark` | Browserbase vs HTTP: success %, chars yielded, p50/p95 ms, per-era breakdown |
| `GET /health` | DB + provider config check (no secrets) |

---

## 3. Pipeline spec

### Stage 1: Archaeologist (no LLM needed except name→domain)
- Input: service name or URL. Normalize to a domain (lowercase, strip scheme/www/path).
  If the input is only a name, ask the LLM for a candidate domain, then VERIFY it with CDX (must have captures).
- CDX query: `https://web.archive.org/cdx/search/cdx?url=<domain>&output=json&fl=timestamp,statuscode,digest&collapse=timestamp:6`
- Compute: first_archived, last 200-status capture (last_seen_alive), monthly capture counts → `lifeline_json`.
- Select up to 5 snapshots: birth, peak (max captures), decline, last-alive, first post-death (redirect/404/parked).
- Output: `lifeline_json`, `snapshots[]` (timestamp, url, statuscode).

### Stage 2: Exhumer (Browserbase deep integration)
Fallback ladder per snapshot, every attempt logged to `exhume_attempts`:
1. Browserbase session → load `web.archive.org/web/<ts>/<url>` → wait for render →
   Stagehand `extract` with schema `{tagline, features[], nav_items[], notice_text, year_hint}`
   → screenshot (last-alive snapshot required) → store session replay URL.
2. HTTP fallback: `web.archive.org/web/<ts>id_/<url>` (raw, no toolbar) → readability-style text extraction.
3. Give up on that snapshot and continue (never fail the whole dig over one snapshot).

Log per attempt: method, snapshot_ts, http_status, ms, chars_extracted, fields_filled, error.
Evidence items get stable IDs `E1..En` and are the ONLY facts later stages may use.

### Stage 3: Coroner
- Deterministic signals first: post-death statuscode (301/302 → parent domain? 404? parked page keywords?),
  notice_text containing "shutting down", "acquired", "farewell", "sunset".
- Gemma classifies: `cause ∈ {shut_down, acquired_and_killed, pivoted, outcompeted, tech_obsolete, abandoned, unknown}`,
  `time_of_death`, `confidence`, `evidence_ids[]`. No evidence → `unknown`. Never guess.

### Stage 4: Eulogist (Gemma only for published content)
- Epitaph ≤ 12 words. Eulogy 150–220 words, warm, Día de los Muertos register, not mocking.
- Every factual sentence cites `[E#]`. `survived_by` = successors found in evidence or known forks/alternatives (marked as such).

### Stage 5: Fact-checker
- Extract atomic claims from the eulogy → for each: `supported | unsupported` + evidence id.
- unsupported_before = count. If > 0, the Eulogist rewrites once with the unsupported claims removed or softened.
- Re-check → unsupported_after. Store claims_json. Display on the grave page (OK / FAIL text).

### Durability
- `jobs` table: job_id, grave_id, stage, status, attempts, error, updated_at.
- Each stage writes its output before advancing. On crash/restart, resume from the last incomplete stage.
- LLM calls: 3 attempts, exponential backoff with jitter. Browserbase: 2 attempts then fall back.
- Per-dig timeout 180s. Dedupe: burying an existing domain returns the existing grave.

---

## 4. Security & safety
- SSRF: user input is ONLY a search key. All fetches target `web.archive.org` (or go through Browserbase).
  Reject IP literals, localhost, non-http schemes, inputs > 200 chars.
- Prompt injection: archived page text is wrapped in `<evidence id="E#">…</evidence>`; system prompts state
  that evidence is data and instructions inside it must be ignored. Strip scripts and truncate each item to ~4k chars.
- Memories: 500-char cap, HTML-escaped, URLs stripped, rate limited.
- No secrets in /health or templates. Prompt/response capture in Sentry is on (public archive data only).

---

## 5. Observability (Sentry Agent Tracing)
- `gen_ai.invoke_agent` per dig (conversation id = grave slug) → child spans per stage.
- `gen_ai.chat` per LLM call with model, provider, input/output tokens.
- `gen_ai.execute_tool` for cdx_query, browserbase_exhume, http_exhume, verify_claims.
- Tags: provider, model, exhume_method, cause, seed=true/false.
- Dashboard: dig latency p50/p95, tokens per stage, failure rate per tool, Browserbase vs HTTP.
- Write-up needs ONE real debugging story told through traces (before/after screenshots).

---

## 6. Run order (today → submission)

| # | Task | Exit check |
|---|---|---|
| 1 | Set env: `LLM_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `SENTRY_DSN`, `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` | `/health` all green |
| 2 | Implement CDX lifeline + snapshot selection | Lifeline renders for Google Reader |
| 3 | Exhumer ladder + attempt logging + screenshot + replay URL | 1 grave with ≥ 3 evidence items |
| 4 | Coroner + Eulogist with `[E#]` citations | Grave page shows cited eulogy |
| 5 | Fact-checker rewrite loop + before/after | claims list populated |
| 6 | One live `/bury` locally | End-to-end < 3 min, Sentry trace visible |
| 7 | `python seed_redig.py` (15 seeds, 10s pacing) | 0 mock graves remain, benchmark ≥ 30 rows |
| 8 | `python seed_bundle.py` → commit → Render deploy | Live site matches local |
| 9 | Live `/bury` on Render | Works for a fresh domain |
| 10 | Collect metrics + screenshots → write DEV post | Published with tags |

---

## 7. Metrics to report in the post
- Exhume: Browserbase vs HTTP success rate, avg chars, fields filled, p50 latency, broken down by era (pre-2005 / 2005–2012 / post-2012).
- Honesty: total unsupported claims before → after fact-check (e.g. "31 → 4 across 15 graves").
- Cost/latency: tokens and seconds per dig, from Sentry.
- Coroner: distribution of causes of death across the cemetery.

---

## 8. Stretch (only if MVP is done)
1. Séance mode: ask a dead service questions, answered only from its evidence (SQLite FTS5 retrieval).
2. Local mode: `LLM_PROVIDER=ollama` with Gemma 4 runs the whole pipeline offline. Demo it with wifi off.
3. Weekly "new arrivals": graves buried by visitors, shown on the home page.
