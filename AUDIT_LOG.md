# Graveyard of Dead Software – Build Audit Log

**Date:** 2026-10-30
**Branch / state:** post-UI redesign, provider switch scaffolded, run tooling added

## What was built

### Core app
FastAPI + Jinja2 + SQLite + 5-stage agentic pipeline
Archaeologist → Exhumer → Coroner → Eulogist → Fact-checker
Routes: `/`, `/grave/<slug>`, `POST /bury`, `/job/<id>`, `POST /marigold/<slug>`, `POST /memory/<slug>`, `/benchmark`, `/health`

### T1. Archaeologist — real Wayback data (COMPLETE)
- `cdx_has_captures(domain)` — CDX check with 15s timeout, 2 retries; rejects if zero captures
- `_cdx_fetch(url, params)` — retry logic with exponential backoff
- `wayback_snapshots(url, n)` — returns newest-first snapshots
- `wayback_first_snapshot(url)` — oldest capture
- `build_lifeline(url)` — year→count map via CDX collapse
- `select_strategic_snapshots(snapshots, lifeline)` — picks birth/peak/decline/last-alive (max 5)
- `full_dig` Stage 1: domain verification, strategic snapshots, lifeline JSON stored

### T2. Exhumer — Browserbase + fallback ladder (COMPLETE)
- `_exhume_with_browserbase_inner(archive_link, slug)` — Browserbase session, screenshot saved to `static/screenshots/<slug>.png`, Stagehand-style structured extraction (`STAGEHAND_SCHEMA`), `fields_filled` count, `evidence_id` per call
- `exhume_with_browserbase(link, slug)` — Sentry `execute_tool` span wrapper
- `_http_fetch_inner` / `exhume_without_browser` — plain HTTP fallback with evidence fields
- `exhume_best(snapshots, use_browserbase, slug)` — walk-back with evidence IDs E1..En, method/status/ms/chars/fields_filled/error per attempt; one failing snapshot never fails the dig
- `database.Grave.extracted_fields_json` — new column for Stagehand extracted fields
- `app.grave_from_result` — stores screenshot path, extracted_fields_json, exhume_attempts

### UI Redesign – Dia de los Muertos ofrenda
- `static/style.css` rebuilt — CSS vars, no shadows/blurs/neon, no forbidden colors, no emojis, border-radius 0 except tombstone arch
- Lifeline rendered as inline SVG marigold sparkline on `grave.html`
- All templates cleaned of emojis, icons as inline SVG

### LLM provider & observability
- `pipeline.py` — `LLM_PROVIDER` (gemini|groq|ollama), `_ask_gemini` with 3-attempt backoff, `traced_chat` provider tag
- `.env.example` updated

### Run & measure tooling
- `seed_redig.py`, `render.yaml`, `seed_bundle.py`

## What is working
- App boots, DB init, static serving
- All routes render with new design, JS polling, marigold, memory work
- Rate limiting on /bury and /memory
- Sentry SDK init present, span wiring for gen_ai.invoke_agent / chat / execute_tool
- UI meets all hard rules, SVG icons, CSS variables
- T1 Archaeologist: real CDX data, domain verification, strategic snapshots, lifeline JSON, SVG sparkline on grave page
- T2 Exhumer: Browserbase session + screenshot + Stagehand extract, HTTP fallback, evidence IDs E1..En, fields_filled tracking, walk-back resilience
- Provider abstraction and tooling scripts ready

## What is NOT working / not exercised
- No live LLM calls. LLM_PROVIDER defaults to ollama, GEMINI_API_KEY empty, SENTRY_DSN empty
- Benchmark table has 0 rows
- 15 seed graves are static mock records from seed.json — no screenshots, replays, lifelines, exhume attempts, claims
- Sentry silent – no DSN
- seed_redig.py and seed_bundle.py not yet executed
- Browserbase path requires BROWSERBASE_API_KEY
- T4-T8 not yet started (Fact-checker loop, Durability, Sentry polish, Seeds+deploy, Metrics script)

## Demo / mock data
seed.json 15 graves with hand-written epitaphs/eulogies/causes:
Google Reader, GeoCities, Vine, Grooveshark, Adobe Flash, MySpace, Yahoo Answers, Picnik, Digg, ICQ, del.icio.us, AIM, Google+, Zune, Tumblr
All dates, marigold counts, survived_by are curated demo copy. Lifeline, screenshot, replay, evidence, claims empty until seed_redig.py runs.

## Next actions planned (per WORKFLOW.md priority order)
1. T3: Coroner + Eulogist with citations — Pydantic validation, [E#] citations, evidence tags in prompts, "Eulogy written by <model>"
2. T4: Fact-checker loop — claims extraction, verify against evidence, rewrite unsupported, OK/FAIL rendering, claims_json/unsupported_before/after
3. T5: Durability — per-stage job persistence, 180s per-dig timeout, SSRF guard, memories 500-char cap + HTML escape + URL strip
4. T6: Sentry polish — conversation id = slug, tags provider/model/exhume_method/cause/seed, token usage per chat span, no crash without DSN
5. T7: Seeds + deploy — idempotent seed_redig.py (--force), seed_bundle.py, render.yaml all env vars, README disk-reset note
6. T8: Metrics script — scripts/metrics.py markdown tables (exhume comparison, unsupported before→after, cause distribution, avg tokens/seconds)
7. Set env vars, run live /bury, run seed_redig.py, deploy to Render

## Files changed/added
- static/style.css – redesign
- templates/base.html, cemetery.html, grave.html – emoji removal/SVG
- pipeline.py – provider switch, Gemini client, retry
- .env.example – new vars
- seed_redig.py – re-dig script
- render.yaml – Render config
- seed_bundle.py – export bundle
- AUDIT_LOG.md – this file
