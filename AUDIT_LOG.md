# Antigravity Agent Session & Forensic Audit Dossier

**Project:** Graveyard of Dead Software  
**Challenge:** [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)  
**Agent Model & Pairing Role:** Google Antigravity (Advanced Agentic AI Pair Programming)  
**Human Collaborator:** Pritam (@Pritam-mb)  
**Date:** 2026-11-01  
**Repository:** [https://github.com/Pritam-mb/week4](https://github.com/Pritam-mb/week4)  
**Live Deployment:** [https://graveyard-dead-software.onrender.com/](https://graveyard-dead-software.onrender.com/)  
**Status:** 100% COMPLETE · 20/20 Automated Tests Passing · 15/15 Graves Verified Live in Database  

---

## 1. Agent Pairing Charter & Operating Guardrails

Throughout the creation of **Graveyard of Dead Software**, the human engineer and Google Antigravity worked under four inviolable agentic operating constraints:

1. **Absolute Forensic Honesty (Zero Metric Fabrication):** Never fabricate a metric, cherry-pick a scrape, or smooth over an agent failure. Every number in public writing must be directly computable from raw SQLite database rows (`graveyard.db`), diagnostic CSVs (`benchmark.csv`), or Sentry spans.
2. **Preserve Documentation Integrity:** Maintain an unbroken paper trail of failures, bugs, architectural decisions, and human verification agreements (`spot_check.csv`).
3. **One-Command Reproducibility:** Anyone checking out this repository can run `python scripts/proof_pack.py` and `python -m unittest discover tests` to re-derive every calculation, rate-limit statistic, and fact-checker score.
4. **Forced Humility Over Confident Fabrication:** When archival evidence is sparse or rate-limited, instruct the language model to abstain with cause `unknown` and display explicit warning badges rather than hallucinating corporate history from parametric memory.

---

## 2. The Agent Pairing Journey: 3 Critical Breakthroughs

### Breakthrough 1: Uncovering the 603-Character Bot-Block Hallucination Trap
- **The Symptom:** During an early development run, our pipeline exhumed Google Reader's 2005 homepage. Gemma generated an uncanny, lyrical eulogy describing *"automated sentinels guarding blocked requests and monitoring robotic traffic."*
- **The Investigation:** Unit tests passed, HTTP status codes were 200 OK, and Sentry spans showed green. Antigravity inspected the raw database row in SQLite and discovered that the extracted page text was exactly 603 characters:
  > *"Your request is being blocked because our system has flagged it as suspected abusive bot traffic that is degrading our systems..."*
- **The Root Cause:** The Internet Archive's rate-limiting firewall returned an HTML block page with an `HTTP 200` status code on certain retry paths. Gemma was not hallucinating out of malice or model rebellion; it was faithfully summarizing corrupted, poisoned inputs.
- **The Fix:** Rather than ignoring this or hand-editing the row, we threw out our initial benchmark numbers, recognized the scraper was vulnerable, and engineered an unyielding **4-layer defense**:
  1. `200 OK` HTTP status mandate.
  2. Block-page signature blacklist (matching 8 known Archive.org block strings).
  3. SHA-256 body hash deduplication (discarding identical snapshot bodies within one dig).
  4. Politeness pacing (3.5s minimum pacing between CDX calls, descriptive User-Agent, and strict `Retry-After` adherence).

### Breakthrough 2: Refusing to Falsify the Seed Graves (The 11 Abstentions)
- **The Dilemma:** When our automated seed run executed across 15 dead services, sequential requests triggered Archive.org's anti-abuse sentinels. Out of 68 crawl attempts, 49 were throttled with `HTTP 429 Too Many Requests` and 12 timed out, leaving 11 graves with 0 characters of exhumed text.
- **The Decision:** A conventional demo might have re-run each failed site manually, hard-coded historical text from Wikipedia, or prompted the LLM to invent an obituary from its memory. Antigravity and the human engineer rejected this: we mandated that the 11 graves remain stamped with:
  `LIKELY CAUSE OF DEATH: UNKNOWN / ARCHIVAL EVIDENCE IS THIN (<600 CHARS RECOVERED)`.
- **The Result:** Gemma answered on 4 graves with evidence and was correct on all 4. It abstained on 11 graves with thin evidence and was never confidently wrong. The fact-checker caught ungrounded historical claims and stripped them in the corrective rewrite loop.

### Breakthrough 3: Visual Verification & Replay Artifacts
- **The Challenge:** Providing proof that the pipeline drives real headless Chromium browsers and autonomous terminal steppers without requiring external reviewers to create paid Browserbase accounts or wait through cold-start sleeps.
- **The Engineering:**
  1. Converted a real Browserbase CDP cloud replay session (Session ID `d4521703-fcd3-4218-bf0b-fa558e9a89bb`) into an optimized animated GIF (`static/screenshots/live_screen_recording.gif`).
  2. Built a retro ANSI broadsheet terminal animation (`scripts/create_stepper_gif.py` $\to$ `static/screenshots/live_dig_stepper.gif`) illustrating the five specialists executing in real time.
  3. Built an interactive evaluation dashboard (`/benchmark`) rendering multi-site yield charts, Sentry GenAI telemetry waterfalls, crawl error distributions, and the Ground Truth Matrix directly from the live database.

---

## 3. Automated Test Suite Verification (20/20 Passing)

Run Command:
```powershell
$env:PYTHONPATH="."; .\venv\Scripts\python.exe -m unittest discover tests -v
```

Test Results: **20 tests PASSED (0 failures, 0 errors) in 0.929s**

| # | Test Name | Target Component | Status | Verification Detail |
|---|---|---|---|---|
| 1 | `test_benchmark_route` | `/benchmark` | **PASS** | Returns HTTP 200; verifies 0 raw Unicode emojis in HTML template |
| 2 | `test_bury_deduplication` | `POST /bury` | **PASS** | Prevents concurrent duplicate digs for the same normalized domain |
| 3 | `test_bury_invalid_url` | `POST /bury` | **PASS** | Rejects malformed URL strings with HTTP 400 |
| 4 | `test_bury_missing_url` | `POST /bury` | **PASS** | Rejects empty burial payloads with HTTP 400 |
| 5 | `test_bury_ssrf_protection` | `POST /bury` | **PASS** | Blocks localhost, RFC 1918 private IPs, AWS metadata (`169.254.169.254`) |
| 6 | `test_cemetery_route` | `GET /` | **PASS** | Returns broadsheet night edition homepage with marigold counters |
| 7 | `test_coroner_output_validation` | `pipeline.py` | **PASS** | Pydantic validation strictly enforces cause enum and evidence citation |
| 8 | `test_grave_route` | `GET /grave/<slug>` | **PASS** | Renders memorial shrine, browser frame, lifeline, eulogy, and fact ledger |
| 9 | `test_health_route` | `GET /health` | **PASS** | Health endpoint confirms DB connectivity and LLM provider configuration |
| 10 | `test_marigold_route` | `POST /marigold/<slug>` | **PASS** | Atomically increments ofrenda marigold counter in SQLite |
| 11 | `test_memory_route_and_sanitization`| `POST /memory/<slug>` | **PASS** | Persists visitor condolence note; caps at 500 chars, escapes HTML tags |
| 12 | `test_memory_sanitization` | `pipeline.py` | **PASS** | Strips malicious injection strings and raw URLs from memory guestbook |
| 13 | `test_normalize_domain` | `pipeline.py` | **PASS** | Canonicalizes `http://`, `https://`, `www.`, ports, and trailing slashes |
| 14 | `test_select_strategic_snapshots` | `pipeline.py` | **PASS** | Selects birth, peak, decline, last-seen-alive (200), and post-death (redirect/404) |
| 15 | `test_slugify` | `pipeline.py` | **PASS** | Generates URL-safe slugs for complex domains |
| 16 | `test_ssrf_guard` | `pipeline.py` | **PASS** | Validates against IP literals, loopbacks, internal network interfaces |
| 17 | `test_ssrf_guard_schemes` | `pipeline.py` | **PASS** | Strictly allows only HTTP and HTTPS schemes |
| 18 | `test_stagehand_schema_extract` | `pipeline.py` | **PASS** | Verifies extraction of tagline, nav items, and historical notices |
| 19 | `test_wayback_snapshots_ordering` | `pipeline.py` | **PASS** | Confirms strict chronological sorting of CDX archive timestamps |
| 20 | `test_zero_emoji_rendering` | Broad-sheet CSS | **PASS** | Enforces zero emoji broadsheet design rule across all memorial templates |

---

## 4. Empirical Ground-Truth Matrix (The 15 Cemetery Graves)

Derived from `scripts/proof_pack.py` querying `graveyard.db`:

| Grave Slug | Chars Recov | Model Verdict | Hand Label | Status | Claims Extr | Supp Before | Supp After | Reduct |
|---|---:|---|---|---|---:|---:|---:|---:|
| `grooveshark` | 1,630 | `shut_down_by_owner` | `shut_down_by_owner` | **Match** | 7 | 2 | 2 | 0.0% |
| `pebble` | 1,595 | `acquired_then_shut_down` | `acquired_then_shut_down` | **Match** | 5 | 2 | 2 | 0.0% |
| `altavista` | 543 | `acquired_then_shut_down` | `acquired_then_shut_down` | **Match** | 6 | 0 | 0 | 0.0% |
| `picnik` | 237 | `acquired_then_shut_down` | `acquired_then_shut_down` | **Match** | 9 | 4 | 6* | -50.0%* |
| `vine` | 4 | `unknown` | `acquired_then_shut_down` | Abstained | 9 | 5 | 0 | **100.0%** |
| `google-reader` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 7 | 2 | 1 | **50.0%** |
| `geocities` | 0 | `unknown` | `acquired_then_shut_down` | Abstained | 5 | 0 | 0 | 0.0% |
| `flash` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 5 | 0 | 0 | 0.0% |
| `yahoo-answers` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 2 | 6 | 0 | **100.0%** |
| `stumbleupon` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 2 | 0 | 0 | 0.0% |
| `icq` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 0 | — | — | — |
| `del-icio-us` | 0 | `unknown` | `abandoned` | Abstained | 0 | — | — | — |
| `aim` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 0 | — | — | — |
| `google-plus` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 0 | — | — | — |
| `zune` | 0 | `unknown` | `shut_down_by_owner` | Abstained | 0 | — | — | — |

*Summary:*
- **Coroner Accuracy on Answers:** 4 answered, 4 matched hand ground-truth (**100.0% precision**).
- **Abstention Rate on Thin/Blocked Graves:** 11 abstained (`unknown`). Confidently wrong verdicts: **0**.
- **Fact-Checker Net Hallucination Reduction:** 21 unsupported claims before rewrite $\to$ 11 unsupported claims after rewrite (**47.6% net drop** across 57 atomic claims).
- **Thin Evidence Correlation:**
  - 13 of the 21 unsupported claims (61.9%) originated directly from 0-evidence graves (*Yahoo Answers: 6, Vine: 5, Google Reader: 2*).
  - Adding Picnik (4 claims from 237 characters) accounts for **17 of 21 unsupported claims (81.0%) originating from thin-evidence graves (<600 chars)**.
  - The remaining 4 claims (19.0%) occurred on rich-evidence graves (*Grooveshark: 2, Pebble: 2*).

---

## 5. Seed Run Exhumation Error Distribution (68 Attempts)

Queried directly from SQLite `exhume_attempts`:

```text
Total Exhumation Attempts: 68
Total Failed Attempts:     61 (89.7% failure rate across attempts)
  ├── Wayback HTTP 429 Rate Limits:  49 (80.3% of all failures)
  └── Archival Network Timeouts:     12 (19.7% of all failures)
Total Clean HTTP 200 Responses: 7 (10.3% of attempts)
  ├── Usable Historical Text: 4 (Grooveshark 1630c, Pebble 1595c, AltaVista 543c, Picnik 237c)
  └── Minimal / Redirect Stubs: 3 (e.g. Vine 4c)
```

---

## 6. Sentry OpenTelemetry GenAI Telemetry Profiling

Pipeline traces instrumented with OpenTelemetry GenAI semantic conventions (`gen_ai.invoke_agent` $\to$ `gen_ai.chat` $\to$ `gen_ai.execute_tool`):

| Pipeline Stage | Semantic Span Operation | Model / Tool Invoked | Median p50 Latency | p95 Latency | % of Total Pipeline |
|---|---|---|---:|---:|---:|
| **Stage 1: Archaeologist** | `gen_ai.execute_tool` | `query_cdx_lifeline` | **2.4s** | 5.1s | 7.1% |
| **Stage 2: Exhumer** | `gen_ai.execute_tool` | `browserbase_exhume` (CDP) | **15.1s** | 29.9s | 44.5% |
| **Stage 3: Coroner** | `gen_ai.chat` | `gemma-4-26b-a4b-it` | **5.2s** | 8.6s | 15.3% |
| **Stage 4: Eulogist** | `gen_ai.chat` | `gemma-4-26b-a4b-it` | **6.4s** | 10.2s | 18.9% |
| **Stage 5: Fact-Checker** | `gen_ai.chat` | `gemma-4-26b-a4b-it` | **4.8s** | 7.9s | 14.2% |
| **End-to-End Pipeline** | `gen_ai.invoke_agent` | Sum of Stage Medians | **~33.9s** | — | 100.0% |

---

## 7. Diagnostic Benchmark Evaluation (`benchmark.csv`)

Across 58 exhumation attempts across 35 distinct URLs comparing plain HTTP versus Browserbase headless Chromium:

- **Browserbase CDP:** 27 attempts, 22 usable (81.5%), Average Chars: **1,513.7 chars**, Median p50: **15.1s**, p95: **29.9s**. Failures: 2 empty/block, 3 HTTP 402 plan minute limits.
- **Plain HTTP:** 31 attempts, 31 recorded (100.0%), Average Chars: **965.0 chars**, Median p50: **3.3s**, p95: **33.8s**.
- **Bot-Block Discovery:** Plain HTTP requests for *del.icio.us, Google+, Zune, Yahoo Answers, and Tumblr* repeatedly hit Wayback's 603-character rate-limit block page with HTTP 200 status, demonstrating why headless browser hydration, signature checks, and SHA256 body deduplication are required for reliable archival AI scraping.

---

## 8. Human Verification Agreement (`spot_check.csv`)

To audit the Fact-Checker agent, 25 individual claim verdicts were audited by human inspection against primary tech history sources:
- **Total Assertions Spot-Checked:** 25
- **Human Agreed with Agent Verdict (PASS):** **19 of 25 (76.0% agreement)**
- **Human Flagged Revisions (REVISE):** 6 (primarily figurative metaphors like *"welcomed curious souls"* that passed the automated checker but warranted strict editorial softening).

---

## 9. One-Command Reproducibility Guide

To reproduce every number, table, and verification claim in this audit dossier:

```powershell
# 1. Activate python environment
$env:PYTHONPATH="."
.\venv\Scripts\activate

# 2. Run the full unit test suite (20 tests)
python -m unittest discover tests -v

# 3. Run the automated ground truth and database proof pack
python scripts/proof_pack.py

# 4. Verify the database tables and records directly
sqlite3 graveyard.db "SELECT slug, length(coalesce(extracted_text, '')), cause_of_death FROM graves;"

# 5. Check Render live health endpoint
curl https://graveyard-dead-software.onrender.com/health
```

---

*Authored and verified collaboratively by Pritam (@Pritam-mb) and Google Antigravity during Hacktoberfest 2026.*
