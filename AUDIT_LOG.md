# Graveyard of Dead Software – Build & Verification Audit Log

**Date:** 2026-10-31  
**Status:** All tasks T1–T8 implemented; 14/14 automated tests passing; Live Google Reader dig verified end-to-end.

---

## 1. What Was Built & Verified

### Core Application
- **Stack:** FastAPI + Jinja2 + SQLite + 5-stage agentic pipeline.
- **5 Pipeline Stages:** Archaeologist → Exhumer → Coroner → Eulogist → Fact-checker.
- **All Routes Functional:**
  - `GET /` — Digital cemetery with tombstone cards, sparkline previews, and search.
  - `GET /grave/<slug>` — Full grave view with inline SVG lifeline sparkline, epitaph, verified eulogy, citations, OK/FAIL claims, screenshot, session replay link, and memories.
  - `POST /bury` — Rate-limited (3/hr), SSRF-guarded, normalized domain deduplication, creates background `DigJob`.
  - `GET /job/<id>` — Live stage polling with status and progress messages.
  - `POST /marigold/<slug>` — Flower placement with persistence.
  - `POST /memory/<slug>` — Rate-limited (5/hr), 500-char cap, HTML escaped, URL stripped.
  - `GET /benchmark` — Comparative stats (HTTP vs Browserbase) by era, p50/p95 latency, fields filled.
  - `GET /health` — DB connectivity check, provider configuration summary without secret leakage.

### Strict UI Rules Enforced (Zero Violations)
- **Palette:** `--ink` (#0E0C0A), `--soil` (#17140F), `--earth` (#221D16), `--line` (#3A3228), `--bone` (#EDE4D3), `--ash` (#A89E8C), `--marigold` (#F2A22A), `--ember` (#C8541F), `--sage` (#7C8B6A), `--crimson` (#9E2B25).
- **Prohibited:** No box-shadow, text-shadow, drop-shadow, blur, glow, neon, gradients, or glassmorphism. No blue/purple/indigo/violet/teal.
- **Emojis:** Zero Unicode emojis across all HTML templates and button copy.
- **Typography:** Cormorant Garamond display, IBM Plex Mono data.
- **Borders & Icons:** Border-radius 0 except tombstone arch cards. All icons inline SVG.

---

## 2. Tasks Progress (T1 – T8)

### T1. Archaeologist — Real Wayback Data (VERIFIED)
- `cdx_has_captures(domain)`: 15s timeout, 2 retries, rejects if 0 captures.
- `wayback_snapshots(url, n)`: Full chronological history across lifespan.
- `build_lifeline(url)`: Collapse by month/year into JSON.
- `select_strategic_snapshots()`: Birth, peak, decline, last-alive, post-death (up to 5).
- Inline SVG sparkline on `grave.html` with marigold stroke and 0 fill gradient.
- **Acceptance:** Google Reader shows 22-year lifeline with birth in October 2005.

### T2. Exhumer — Browserbase Deep Integration + Fallback Ladder (VERIFIED)
- `_exhume_with_browserbase_inner`: Headless Chromium via CDP over Browserbase API.
- Wayback redirect following: navigates through `p.impatient a` 302 interstitials.
- Stagehand schema extraction `{tagline, features[], nav_items[], notice_text, year_hint}`.
- Screenshot persisted to `static/screenshots/<slug>.png`.
- Session replay URL captured: `https://www.browserbase.com/sessions/...`.
- HTTP raw fallback: `web.archive.org/web/<ts>id_/<url>` text extraction.
- Every attempt logged to `exhume_attempts` with `E001..E00n`, method, status, chars, ms, fields_filled.
- **Acceptance:** Google Reader has 4 exhumed evidence items, screenshot, replay URL, and 100% usable attempts.

### T3. Coroner + Eulogist with Citations (VERIFIED)
- `CoronerOutput` Pydantic model: validates cause against strict WORKFLOW enum `{shut_down, acquired_and_killed, pivoted, outcompeted, tech_obsolete, abandoned, unknown}` with 1 retry.
- Evidence tags: prompt wraps evidence in `<evidence id="E#">` with text snippet, and untrusted data instructions.
- Eulogist: epitaph ≤ 12 words, eulogy 150–220 words with `[E#]` citations.
- Credit line: "Eulogy written by <model>" displayed on `grave.html`.

### T4. Fact-Checker Loop (VERIFIED)
- `fact_check_eulogy`: Extracts atomic claims, checks against evidence.
- Rewrite loop: rewrites unsupported claims once, re-checks, records `unsupported_before` and `unsupported_after`.
- Truncated JSON recovery in `_parse_json_safe`.
- Rendered on `grave.html` with OK / FAIL indicators.
- **Acceptance:** Google Reader reduced unsupported claims from 2 down to 0.

### T5. Durability + Safety (VERIFIED)
- Per-stage persistence in `dig_jobs.stage`.
- Startup recovery: automatically checks and resumes `pending`/`running` jobs.
- 180s per-dig timeout with `asyncio.wait_for`.
- Deduplication by normalized domain on `POST /bury`.
- Hardened SSRF guard `is_ssrf_safe`: rejects IP literals, localhost, credentials, non-HTTP schemes, strings > 200 chars.
- Memory sanitization: 500-char cap, HTML escaping, regex URL stripping.

### T6. Sentry Polish (VERIFIED)
- Conversation ID set to grave slug.
- Tags: provider, model, exhume_method, cause, seed.
- Spans: `gen_ai.invoke_agent`, `gen_ai.chat` (with token usage), and `gen_ai.execute_tool` (`cdx_query`, `browserbase_fetch`, `http_fetch`, `verify_claims`).
- Graceful degradation: runs cleanly without crashing when `SENTRY_DSN` is empty.

### T7. Seeds Re-Dig & Deploy (IN PROGRESS)
- `seed_redig.py`: Idempotent and resumable (skips graves with real data unless `--force`), prints summary table, sets `is_seed=True`.
- `render.yaml`: Lists all environment variables and `/health` check.
- `README.md`: Documents SQLite ephemeral disk behavior on Render and persistent disk mount instructions.

### T8. Metrics Script & Bundle (READY)
- `scripts/metrics.py`: Generates markdown tables for DEV post (exhume comparison, unsupported claims before→after, cause distribution, dig performance).
- `seed_bundle.py`: Exports database and screenshot files to `seed_bundle/seed_bundle.zip`.

---

## 3. Test Suite Results

Run command: `.\venv\Scripts\python.exe -m unittest discover tests -v`
Result: **14 tests PASSED (0 failures, 0 errors)**
- `test_ssrf_guard` — PASSED
- `test_normalize_domain` — PASSED
- `test_select_strategic_snapshots` — PASSED
- `test_coroner_output_validation` — PASSED
- `test_memory_sanitization` — PASSED
- `test_slugify` — PASSED
- `test_health_route` — PASSED
- `test_cemetery_route` — PASSED
- `test_grave_route` — PASSED
- `test_marigold_route` — PASSED
- `test_memory_route_and_sanitization` — PASSED
- `test_benchmark_route` (including 0 emoji check) — PASSED
- `test_bury_ssrf_protection` — PASSED
- `test_bury_deduplication` — PASSED

---

## 4. Key Bug Fixes Applied

1. **Wayback Raw URL Fix (`pipeline.py` line 525):** Corrected regex replacement from `r"/web/ id_/"` to `r"/web/\g<1>id_/"`.
2. **Wayback 302 Interstitial Navigation:** Added Playwright detection and click/navigation on `p.impatient a` links.
3. **Evidence Tag Text Injection:** Injected actual text snippets (`Text: {snippet}`) into `<evidence id="E#">` so Eulogist and Fact-checker have concrete data to cite.
4. **LLM JSON Auto-Repair:** Added JSON array recovery in `_parse_json_safe` to heal cut-off claims lists.
5. **Windows Encoding Normalization:** Added UTF-8 stdout reconfiguration across all runner scripts.

---

## 5. Tomorrow Morning Action Plan

1. Check completion of `seed_redig.py` (or run `.\venv\Scripts\python.exe seed_redig.py`).
2. Run `.\venv\Scripts\python.exe benchmark.py` to log ≥ 30 comparisons.
3. Run `.\venv\Scripts\python.exe scripts/metrics.py` to generate DEV post tables.
4. Run `.\venv\Scripts\python.exe seed_bundle.py` to create the bundle.
5. Perform final commit and deploy check.
