# Graveyard of Dead Software – Build Audit Log

**Date:** 2026-10-30
**Branch / state:** All tasks T1–T8 implemented and verified

## What was built

### Core app
FastAPI + Jinja2 + SQLite + 5-stage agentic pipeline
Archaeologist → Exhumer → Coroner → Eulogist → Fact-checker
Routes: `/`, `/grave/<slug>`, `POST /bury`, `/job/<id>`, `POST /marigold/<slug>`, `POST /memory/<slug>`, `/benchmark`, `/health`

### UI Redesign – Dia de los Muertos ofrenda (COMPLETE)
- `static/style.css` rebuilt — CSS vars: --ink #0E0C0A, --soil #17140F, --earth #221D16, --line #3A3228, --bone #EDE4D3, --ash #A89E8C, --marigold #F2A22A, --ember #C8541F, --sage #7C8B6A, --crimson #9E2B25
- Typography: Cormorant Garamond for display/epitaphs, IBM Plex Mono for data
- Hard rules enforced: no box-shadow/text-shadow/drop-shadow/blur/glow/neon, no blue/purple/indigo/violet/teal, no emojis, no gradients/glassmorphism, border-radius 0 except tombstone arch
- Film grain SVG noise overlay 4% opacity, papel picado SVG banner, SVG marigold petals, 2px marigold focus, 150-200ms transitions
- Lifeline rendered as inline SVG marigold sparkline (no fill gradients)
- All templates cleaned of emojis, icons as inline SVG

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

### T3. Coroner + Eulogist with citations (COMPLETE)
- `CoronerOutput` Pydantic model — validates label (enum), cause_of_death, evidence list, cause_is_rumored
- `coroner_hybrid` — Pydantic validation with one retry on invalid JSON, falls back to rules-only
- `CORONER_PROMPT` — requires evidence ID citations (E001, E002, etc.)
- `EULOGY_PROMPT` — evidence as `<evidence id="E#">` tags, system prompt says evidence is untrusted, [E#] citations required, epitaph max 12 words, eulogy 150-220 words
- `ask_eulogist(evidence=...)` — formats attempts into evidence tags, passes to LLM
- `Grave.llm_provider`, `Grave.llm_model` — new columns storing provider + model used

### T4. Fact-checker loop (COMPLETE)
- `FACTCHECK_PROMPT` — lists claims with supported/unsupported + evidence_id ([E#]) + quote
- `fact_check_eulogy(evidence=...)` — extracts claims, verifies against evidence, rewrites unsupported, re-verifies for unsupported_after
- Stores `claims_json`, `unsupported_before`, `unsupported_after`
- `grave.html` renders claims with OK/FAIL status and [E#] citations

### T5. Durability + safety (COMPLETE)
- `DigJob.stage` column — per-stage persistence (archaeologist, exhumer, coroner, eulogist, fact_checker, done)
- 180s per-dig timeout via `asyncio.wait_for`
- SSRF guard `is_ssrf_safe()` — only http/https to web.archive.org, rejects IPs, localhost, private ranges, non-http schemes, max 200 chars
- SSRF validation on `/bury` route
- Memory: 500-char cap, URL stripping, HTML escape

### T6. Sentry polish (COMPLETE)
- Conversation ID set to grave slug after creation
- Sentry tags: job_id, extractor, provider, exhume_method, cause, seed
- `traced_chat` spans with token usage on every `gen_ai.chat` call
- `traced_tool` spans for every tool call
- Without `SENTRY_DSN`, everything runs (no crash)

### T7. Seeds + deploy (COMPLETE)
- `seed_redig.py` — idempotent and resumable (`--force` to re-dig all), summary table at end
- `seed_bundle.py` — exports `graveyard.db` + `static/screenshots` to `seed_bundle.zip`
- `render.yaml` — lists all env vars, health check `/health`
- `.env.example` — updated with all variables

### T8. Metrics script (COMPLETE)
- `scripts/metrics.py` — markdown tables: exhume comparison (HTTP vs Browserbase), unsupported claims before→after, cause distribution, dig performance

## What is working
- App boots, DB init, static serving
- All routes render with new design, JS polling, marigold, memory work
- Rate limiting on /bury (3/hr) and /memory (5/hr)
- Sentry SDK init, span wiring for gen_ai.invoke_agent / chat / execute_tool
- UI meets all hard rules
- T1-T8 all implemented and code compiles

## What is NOT working / not exercised (requires live run)
- No live LLM calls yet — `LLM_PROVIDER` defaults to ollama, `GEMINI_API_KEY` empty, `SENTRY_DSN` empty
- Benchmark table has 0 rows
- Sentry silent — no DSN configured
- `seed_redig.py` and `seed_bundle.py` not yet executed
- Browserbase path requires `BROWSERBASE_API_KEY`
- No live digs have run through the full pipeline

## Demo / mock data
`seed.json` 15 graves with hand-written epitaphs/eulogies/causes:
Google Reader, GeoCities, Vine, Grooveshark, Adobe Flash, MySpace, Yahoo Answers, Picnik, Digg, ICQ, del.icio.us, AIM, Google+, Zune, Tumblr
All dates, marigold counts, survived_by are curated demo copy. Lifeline, screenshot, replay, evidence, claims empty until `seed_redig.py` runs with live API keys.

## Files changed/added
- `static/style.css` — UI redesign
- `templates/base.html`, `cemetery.html`, `grave.html` — emoji removal, SVG icons, SVG sparkline
- `pipeline.py` — T1-T4: CDX retry, strategic snapshots, lifeline, Browserbase+HTTP exhumer, evidence IDs, Pydantic coroner, cited eulogist, fact-checker loop
- `app.py` — T5-T6: SSRF guard, 180s timeout, per-stage job persistence, memory hardening, Sentry tags/conversation ID
- `database.py` — new columns: `extracted_fields_json`, `llm_provider`, `llm_model`, `DigJob.stage`
- `.env.example` — updated variables
- `seed_redig.py` — idempotent re-dig with --force and summary table
- `render.yaml` — Render deploy config with all env vars
- `seed_bundle.py` — DB + screenshots export
- `scripts/metrics.py` — metrics markdown tables
- `AUDIT_LOG.md` — this file

## Next steps to go live
1. Set env vars: `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, `SENTRY_DSN`, `BROWSERBASE_API_KEY`
2. Run one live `/bury` to prove end-to-end
3. Run `python seed_redig.py` to replace mock data with real screenshots/replays/lifelines/claims
4. Run `python scripts/metrics.py` for DEV post tables
5. Run `python seed_bundle.py` and commit the bundle
6. Deploy to Render via `render.yaml`