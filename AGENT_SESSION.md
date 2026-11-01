# Antigravity Agent Session: Graveyard of Dead Software

> **Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine**  
> AI Pair Programming Session: **Google Antigravity** & **Pritam (@Pritam-mb)**  
> Full Audit Dossier & Verification Report: [`AUDIT_LOG.md`](AUDIT_LOG.md)  
> Live Deployment: [https://graveyard-dead-software.onrender.com/](https://graveyard-dead-software.onrender.com/)  

---

## Session Overview & Operational Guardrails

This project was built from scratch using **Google Antigravity** (Advanced Agentic AI pair programming) under four strict operating constraints:
1. **Zero Metric Fabrication:** All metrics, latencies, claim counts, and crawl results must be queried directly from SQLite (`graveyard.db`), diagnostic CSVs (`benchmark.csv`), or Sentry spans.
2. **Preserve Documentation Integrity:** Maintain an unbroken log of bugs, rate limits, failures, and human verification checks (`spot_check.csv`).
3. **One-Command Reproducibility:** Anyone can clone the repo and run `python scripts/proof_pack.py` and `python -m unittest discover tests` to re-derive every number.
4. **Forced Humility:** When archival evidence is sparse or rate-limited by Archive.org, the model must abstain with cause `unknown` and an explicit `<600 chars recovered` warning badge rather than fabricating facts from parametric memory.

---

## 3 Critical Agent Session Moments

1. **Uncovering the 603-Character Bot-Block Hallucination Trap:**
   - Archive.org rate-limiting firewalls returned an HTML block page with `HTTP 200 OK` on retry paths.
   - Gemma faithfully summarized this block notice as Google Reader's authentic 2005 homepage.
   - We recognized that unhardened web scrapers poison downstream LLM archaeology, discarded suspect early benchmark numbers, and engineered a 4-layer defense (HTTP 200 mandate, 8-signature blacklist, SHA-256 body deduplication, and 3.5s politeness pacing).

2. **Refusing to Falsify the Seed Graves (The 11 Abstentions):**
   - Sequential exhumations hit Archive.org rate limits (49 of 68 attempts failed with HTTP 429s and 12 timed out), leaving 11 graves with 0 recovered characters.
   - Rather than manually overriding the results or prompting the LLM to invent corporate history, we enforced that all 11 graves display `cause: unknown` with the yellow thin-evidence alert badge.
   - Gemma answered on 4 graves with evidence (100% precision) and abstained on 11 graves without evidence. The fact-checker stripped ungrounded claims during a 1-pass corrective rewrite loop (47.6% net hallucination drop).

3. **Visual Verification & Artifact Engineering:**
   - Built a real Browserbase CDP cloud session replay animation (`static/screenshots/live_screen_recording.gif`) from session `d4521703-fcd3-4218-bf0b-fa558e9a89bb`.
   - Engineered a 5-stage ANSI terminal stepper GIF (`static/screenshots/live_dig_stepper.gif`) showing Archaeologist, Exhumer, Coroner, Eulogist, and Fact-Checker executing live.
   - Created the `/benchmark` evaluation dashboard rendering multi-site yield charts, Sentry GenAI telemetry, crawl error distributions, and the Ground Truth Matrix.

---

## Verification & Reproducibility Summary

- **Automated Tests:** 20/20 unit tests passing in 0.929s (`python -m unittest discover tests`).
- **Reproducible Proof Pack:** Run `python scripts/proof_pack.py` to inspect database ground truth, fact-checker claim distributions, and crawl attempt error breakdowns.
- **Full Audit Dossier:** For complete tables, Sentry GenAI latency breakdowns, error statistics, and human agreement logs, read the full [`AUDIT_LOG.md`](AUDIT_LOG.md).
