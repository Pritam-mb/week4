---
title: "Graveyard of Dead Software: An Autonomous Agent Exhuming the Internet That Was"
published: false
description: "A 5-stage AI agent that exhumes dead software from the Wayback Machine, classifies cause of death, writes eulogies with Gemma, and fact-checks itself before burial."
tags: "hacktoberfest, gemma, render, browserbase, sentry, python"
cover_image: https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/geocities.png
---

# Graveyard of Dead Software: An Autonomous Agent Exhuming the Internet That Was

> *Vol. I · Night of the Dead Edition · Free to bury · Written by AI from archived pages*

The modern web is built upon the digital fossils of forgotten giants. Search engines that defined the 90s, photo editors that lived entirely in Flash, music discovery apps that revolutionized streaming, and RSS readers whose sudden sunset left millions mourning. 

For **Hacktoberfest DEV Challenge Week 4: "Ghost in the Machine"**, we built **Graveyard of Dead Software** ([GitHub Repository](https://github.com/Pritam-mb/week4)): an agentic digital cemetery where dead software is exhumed from the Wayback Machine, examined by an autonomous coroner, memorialized in a warm *Día de los Muertos* eulogy powered by open-weight **Gemma**, and rigorously fact-checked against archival evidence before burial.

---

## 🏛️ The 5-Stage Agentic Exhumation Pipeline

When a user submits a domain or project name to `POST /bury`, our background worker executes an asynchronous 5-stage pipeline designed for resilience, grounding, and forensic honesty:

```
POST /bury ──► jobs table ──► worker runs 5 stages, each persisted & resumable
                                   │
  1. Archaeologist  CDX API → monthly lifeline sparkline, 5 strategic snapshots
  2. Exhumer        Browserbase (Stagehand extract + screenshot) → HTTP id_ fallback
  3. Coroner        Deterministic redirect/HTTP signals + LLM JSON enum validation
  4. Eulogist       Gemma → epitaph (<=12 words) & eulogy (150-220 words) citing [E#]
  5. Fact-checker   Atomic claim extraction → verify vs evidence → 1-pass rewrite loop
                                   │
                         grave row status=done ──► /grave/<slug>
```

### 1. The Archaeologist (Archive Intelligence)
The Archaeologist queries the Wayback Machine's CDX Server API (`web.archive.org/cdx/search/cdx`) over HTTPS with collapsed monthly aggregates. It establishes the true bounds of the service's lifetime, calculating monthly capture volumes to render a zero-gradient, inline SVG lifeline sparkline. It strategically selects up to 5 critical historical snapshots:
- **Birth:** Earliest verified archival record after launch
- **Peak:** The historical epoch of maximum archive activity
- **Decline:** The downward inflection point in coverage
- **Last Seen Alive:** The final confirmed HTTP 200 operational state
- **Post-Death:** The first redirect, 404, or parked domain tombstone

### 2. The Exhumer (Deep Browserbase Integration)
To extract historical context, the Exhumer navigates historical captures using **Browserbase** sessions over CDP, executing Stagehand schema extraction (`tagline`, `features`, `nav_items`, `notice_text`) and capturing full-page historical screenshots. 

When network latency or rate limits occur, the pipeline seamlessly transitions down an intentional fallback ladder to raw HTTP snapshot scraping (`id_/` endpoints). Every attempt is logged with execution duration, characters yielded, and fields extracted into evidence identifiers (`[E001]`..`[E00n]`).

### 3. The Coroner (Forensic Verdicts Without Hallucination)
The Coroner parses deterministic signals first (e.g. 301/302 redirects to parent acquirers, shutdown notices). An LLM then validates the evidence against a strict Pydantic JSON enum:
`cause ∈ {shut_down, acquired_and_killed, pivoted, outcompeted, tech_obsolete, abandoned, unknown}`.
Crucially: **if the archive holds no definitive shutdown text, the verdict is declared `unknown`. The agent never hallucinates.**

### 4. The Eulogist (Gemma in Día de los Muertos Register)
Powered by open-weight **Gemma**, the Eulogist composes a 12-word epitaph and a 150–220 word commemorative eulogy. The tone avoids cynical mockery in favor of the respectful celebration characteristic of *Día de los Muertos*. Every single factual statement is required to cite its supporting evidence token `[E#]`.

### 5. The Fact-Checker (Self-Correcting Grounding Loop)
Autonomous agents frequently hallucinate historical details. To combat this, our 5th stage extracts atomic claims from the generated eulogy and tests them against the `<evidence>` block. If any ungrounded assertions are found (`unsupported_before > 0`), the Eulogist is given a 1-pass rewrite prompt to soften or excise the claim.

---

## 📊 Live Metrics & Empirical Evaluation

### Exhume Evaluation: HTTP vs Browserbase (58 Historical Attempts)

| Extraction Method | Attempts (N) | Usable Yield % | Avg Characters Extracted | Avg Structured Fields | Average Latency | p50 Latency | p95 Latency |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **HTTP (Raw id_ Fallback)** | 31 | 100.0% | 964 chars | 0.3 | 10.3s | 3,300 ms | 36,700 ms |
| **Browserbase (CDP / DOM)** | 27 | 81.5% | 1,513 chars | 0.1 | 18.6s | 15,100 ms | 30,200 ms |

Browserbase yielded **57% more contextual text depth** (1,513 chars vs 964 chars) by executing client-side JavaScript on modern archives, while the raw HTTP fallback provided ultra-fast resilience for retro, static web pages.

### Fact-Checker Grounding: Elimination of Ungrounded Claims

Across our 15 canonical cemetery seeds:
- **Total Claims Extracted:** 55
- **Ungrounded Claims Before Rewrite:** 21
- **Ungrounded Claims After Rewrite:** 11
- **Net Hallucination Reduction:** **10 ungrounded claims purged or grounded (nearly 50% automated reduction)**

---

## 🪦 The Cemetery: 15 Verified Historical Graves

Every grave in the cemetery represents real archival history, bounded by true launch and death dates:

1. **Google Reader** (2005 – 2013): 147 KB screenshot · 7 claims verified · Model: `gemini-flash-lite-latest`
2. **GeoCities** (1995 – 2009): 230 KB screenshot · 5 claims verified
3. **Vine** (2013 – 2016): 161 KB screenshot · 5 claims verified
4. **Grooveshark** (2007 – 2015): 110 KB screenshot · 4 claims verified
5. **Adobe Flash Player** (1996 – 2020): 228 KB screenshot · 5 claims verified
6. **MySpace** (2003 – 2019): 203 KB screenshot · 6 claims verified (bounded to avoid 1996 domain squatting)
7. **Yahoo Answers** (2005 – 2021): 193 KB screenshot · 2 claims verified
8. **Picnik** (2005 – 2012): 160 KB screenshot · 6 claims verified
9. **ICQ** (1996 – 2024): 43 KB screenshot · 4 claims verified
10. **del.icio.us** (2003 – 2017): 225 KB screenshot · 3 claims verified
11. **AOL Instant Messenger (AIM)** (1997 – 2017): 49 KB screenshot · 4 claims verified
12. **Google+** (2011 – 2019): 51 KB screenshot · 3 claims verified
13. **AltaVista** (1995 – 2013): 27 KB screenshot · 2 claims verified
14. **Microsoft Zune** (2006 – 2015): 44 KB screenshot · 3 claims verified
15. **Pebble** (2012 – 2016): 219 KB screenshot · 2 claims verified

---

## 🛡️ Sentry Distributed Tracing & Observability

Observability was built into every layer using `sentry-sdk`:
- **Distributed Spans:** Every exhumation generates a hierarchical trace tree (`gen_ai.invoke_agent` → `gen_ai.chat` → `gen_ai.execute_tool`).
- **Token Accounting & Latency:** Exact token counts and prompt/completion latencies are recorded on all LLM spans.
- **Contextual Tags:** Every trace is tagged with `slug`, `provider`, `model`, `cause`, and `seed`.
- **Fault-Tolerant:** If `SENTRY_DSN` is absent in local development, the application degrades gracefully with zero exceptions.

---

## 🎨 Hard UI Philosophy: Respecting the Medium

In accordance with the hackathon's strict design principles:
- **Zero Modern Clichés:** No box-shadows, text-shadows, drop-shadows, blurs, glows, neon, gradients, or glassmorphism.
- **Color Palette:** Strictly restrained to CSS variables: `--ink`, `--soil`, `--earth`, `--line`, `--bone`, `--ash`, `--marigold`, `--ember`, `--sage`, and `--crimson`.
- **Typography:** Classic newspaper editorial aesthetic with Cormorant Garamond / Fraunces display headings and IBM Plex Mono tabular data.
- **Accessibility:** 100% SVG inline icons with zero emojis, and full motion suppression under `prefers-reduced-motion`.

---

## 🚀 Deployment on Render

The service is fully containerized and deployable on **Render** via [`render.yaml`](https://github.com/Pritam-mb/week4/blob/main/render.yaml):
- Automated health check at `/health`
- Persistent Disk support documented for permanent SQLite storage across deploys
- Seed bundle import mechanism to hydrate all 15 graves on boot

**GitHub Repository:** [https://github.com/Pritam-mb/week4](https://github.com/Pritam-mb/week4)  
**Detailed Dossier & Proofs:** [EVIDENCE_DOSSIER.md](https://github.com/Pritam-mb/week4/blob/main/EVIDENCE_DOSSIER.md)
yes
