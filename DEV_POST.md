---
title: "Graveyard of Dead Software: An Autonomous Agent Exhuming the Internet That Was"
published: false
description: "A 5-stage AI agent that exhumes dead software from the Wayback Machine, classifies cause of death, writes eulogies with Gemma, and fact-checks itself before burial."
tags: hacktoberfest, gemma, render, browserbase, sentry
cover_image: https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/geocities.png
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)*

# Graveyard of Dead Software: An Autonomous Agent Exhuming the Internet That Was

> *Vol. I · Night of the Dead Edition · Free to bury · Written by AI from archived pages*

---

## What I Built

On July 1, 2013, I opened my browser to find that Google Reader was gone. It wasn’t just an RSS feed reader; it was my morning newspaper, my community, and my curated window into human thought across the open web. Thousands of people held small virtual vigils, shared spreadsheets of export links, and tried to preserve what they could. Ten years later, that grief repeats itself constantly: Vine, GeoCities, Grooveshark, Pebble, StumbleUpon, AltaVista. Digital services vanish overnight, leaving behind broken hyperlinks, 404 tombstones, and fading memories.

For **Hacktoberfest Week 4: "Ghost in the Machine"**, I built **Graveyard of Dead Software** ([GitHub Repository](https://github.com/Pritam-mb/week4)). 

It is an autonomous agentic cemetery where dead software is exhumed from the Wayback Machine, forensically examined by an automated coroner, memorialized in a warm *Día de los Muertos* eulogy written by Google's open-weights **Gemma** model, and rigorously fact-checked against archival evidence before burial. Visitors can walk the cemetery rows, read verified obituaries, watch browser replays of old sites, and leave digital marigolds (*cempasúchil*) on the graves of tools they miss.

<!-- Screenshot: Cemetery Homepage Grid with Marigold Counters and Retro Banners -->
<!-- Add screenshot here: ![Cemetery Homepage](https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/cemetery_home.png) -->

---

## Demo

- **Live Deployed Web Application:** [https://graveyard-dead-software.onrender.com](https://graveyard-dead-software.onrender.com) *(replace with your public Render URL)*
- **Live Interactive Exhumation Replay:** [Browserbase Showcase Session](https://www.browserbase.com/sessions/7700becb-935a-4217-846b-b217a1e99a13)
- **GitHub Repository:** [https://github.com/Pritam-mb/week4](https://github.com/Pritam-mb/week4)

<!-- Screenshot: Grave Detail View for Google Reader showing Lifeline, Cause Card, Verified Claims, and Marigold Button -->
<!-- Add screenshot here: ![Grave Detail View](https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/grave_detail.png) -->

---

## Code

{% github https://github.com/Pritam-mb/week4 %}

The entire codebase is open-source under the MIT License, built with Python (FastAPI + Async SQLite + Jinja2), styled strictly with semantic CSS adhering to a brutalist newspaper aesthetic, and orchestrated without heavy framework bloat.

---

## How I Built It

### 1. The Open-Source AI Architecture

At the heart of the Graveyard is **Gemma** (`gemma-4-26b-a4b-it`), Google’s open-weights model run via the Gemini API endpoints. 

Building around an open-weights model required solving concrete engineering hurdles:
- **No System Instructions or AFC:** Gemma on the API does not accept OpenAI-style `system` instruction blocks or automatic function-calling (AFC) tools without throwing 500 errors. We engineered strict structured user-prompts, injecting schemas directly into the prompt body.
- **Pydantic Schema Enforcement with Retry:** All model outputs (cause classifications, epitaphs, atomic claims, verification tokens) pass through Pydantic validators. If a JSON decode fails or an enum value deviates, an automatic single-retry correction loop parses the error and re-prompts the model.
- **Día de los Muertos Persona:** We deliberately tuned the prompt tone away from snarky, cynical obituaries. Instead, Gemma speaks in the warm, reflective voice of the Mexican Day of the Dead—celebrating the ingenuity of the builders, acknowledging the impermanence of software, and citing evidence tags directly.

```python
# pipeline.py: Invoking Gemma with strict Pydantic parsing & zero system-instruction dependencies
config = types.GenerateContentConfig(
    temperature=0.2,
    response_mime_type="application/json",
)
response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents=user_prompt,
    config=config,
)
data = json.loads(response.text)
return CoronerOutput.model_validate(data)
```

---

### 2. Step-by-Step Feature Walkthrough

When someone submits a URL (e.g. `https://geocities.com`) to `POST /bury`, an asynchronous background worker executes a 5-stage exhumation pipeline:

```
POST /bury ──► jobs table ──► background worker executes 5 stages
                                     │
  1. Archaeologist  CDX API → monthly lifeline sparkline, 5 strategic snapshots
  2. Exhumer        Browserbase (CDP / DOM text extraction + screenshot) → HTTP fallback
  3. Coroner        Deterministic signals + Gemma JSON classification
  4. Eulogist       Gemma → 12-word epitaph & 150-220 word eulogy citing [E#]
  5. Fact-Checker   Atomic claim extraction → verify against evidence → rewrite loop
                                     │
                         grave row status=done ──► /grave/<slug>
```

#### Step 1: The Archaeologist (Archive Intelligence & Lifelines)
The Archaeologist queries the Internet Archive's CDX Server API (`web.archive.org/cdx/search/cdx`) over HTTPS with collapsed monthly aggregates. It establishes the earliest verified capture (birth) and the final operational captures (death).
- **Chunked Temporal Queries:** For massive 90s domains like GeoCities with millions of records, single-query CDX calls time out. We split requests into 5-year chunked windows.
- **Zero-Dependency SVG Sparklines:** Generates an inline, pure SVG sparkline of monthly capture density across the service's entire lifespan.

#### Step 2: The Exhumer (Browserbase Deep Extraction & Screenshots)
The Exhumer retrieves historical web pages from Archive.org. 
- It uses **Browserbase** headless Chromium sessions over Chrome DevTools Protocol (CDP) to render historical pages, execute JavaScript, capture authentic full-page PNG screenshots, and record live session replays.
- If a session encounters rate limits, it falls back to raw HTTP snapshot scraping (`id_/` mode).

#### Step 3: The Coroner (Forensic Autopsy Without Hallucination)
The Coroner determines how and why the software died.
- **Deterministic Signal Parsing:** Checks HTTP 301/302 redirects to parent domains (e.g., Yahoo, Google) and scans for verified shutdown keywords.
- **Domain Normalization Bug Defense:** Early in development, the heuristic compared `final_domain` to `original_domain`. Archive.org URLs resolved with `:80` ports (e.g., `google.com:80`), causing false redirect signals. We added strict port and `www.` stripping so only real domain transfers register.
- **Strict Cause Enum:** Causes are constrained to:
  `{shut_down_by_owner, acquired_then_shut_down, abandoned, taken_over_or_redirected, unknown}`.
- **Honesty Guard:** If evidence is thin or no shutdown notice is found in the archive, the Coroner is forced to output `unknown` with low confidence ($\le 0.3$).

#### Step 4: The Eulogist (Gemma Día de los Muertos Memorial)
Gemma composes a memorable 12-word epitaph and a 150–220 word eulogy. Every factual claim is required to cite its supporting evidence token `[E001]`..`[E00n]`.
- If evidence is thin (<600 characters recovered), the UI flags an **"Archival evidence is thin"** notice, and the model is instructed to write a brief, honest remembrance rather than inventing corporate drama.

#### Step 5: The Fact-Checker (Automated Grounding & Self-Correction)
LLMs love to hallucinate dates and acquisitions. Our 5th stage:
1. Deconstructs the eulogy into atomic factual assertions.
2. Cross-references each assertion against the `<evidence>` text.
3. If unsupported assertions are detected (`unsupported_before > 0`), it triggers a 1-pass rewrite prompt that forces Gemma to remove or soften unverified claims.

<!-- Screenshot: Stepper Progress UI showing Archaeologist, Exhumer, Coroner, Eulogist, and Fact-Checker ticks -->
<!-- Add screenshot here: ![Exhumation Stepper](https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/stepper_progress.png) -->

---

### 3. The Bot-Block Defense: An Accidental Discovery in Agentic Scraping

One of the most fascinating engineering discoveries of this project was what we call the **Bot-Block Hallucination Trap**:

When hammering Archive.org without proper rate-limiting, the Wayback Machine serves an HTTP 429 page containing 603 characters of text:
> *"Your request is being blocked because our system has flagged it as suspected abusive bot traffic that is degrading our systems..."*

In our early runs, because the page returned with an HTML body, our parser ingested this text as the software's real content! The LLM dutifully analyzed this text and composed poetic eulogies about *"automated sentinels guarding blocked requests"* and classified Google Reader's cause of death as a *"cyber defense lockout."*

To permanently defeat this, we engineered a four-tiered **Block-Page Defense** in `pipeline.py`:
1. **HTTP 200 Hard Requirement:** Any non-200 HTTP response is rejected immediately.
2. **Phrase-Blacklist Defense:** Scans for 8 bot-block signatures: `suspected abusive bot traffic`, `overloading our systems`, `too many requests`, `service temporarily unavailable`, etc.
3. **Body Hash Uniqueness:** Maintains a `seen_hashes` set per dig. If multiple snapshots return identical HTML bodies, they are discarded as generic server tombstones.
4. **Archive.org Politeness:** Added a custom User-Agent (`GraveyardOfDeadSoftware/1.0 (+mailto:contact@graveyard.example.com)`), enforced a 3.5-second pacing delay between CDX calls, and implemented exponential backoff (`5 * 2^attempt`) on `Retry-After`.

---

### 4. Sentry Distributed Agent Observability

We instrumented the entire pipeline with `sentry-sdk`, structuring our multi-stage agent according to OpenTelemetry GenAI semantic conventions:
- **Hierarchical Spans:** A single root span `gen_ai.invoke_agent` tracks the entire burial. Child spans `gen_ai.chat` monitor each Gemma inference stage, while `gen_ai.execute_tool` spans wrap the CDX API queries and Browserbase sessions.
- **Granular Token & Model Telemetry:** Every trace captures model name (`gemma-4-26b-a4b-it`), prompt tokens, completion tokens, latency, and extraction success.
- **Fail-Safe Operation:** In local development without a DSN, Sentry degrades gracefully to no-op logging without breaking pipeline execution.

<!-- Screenshot: Sentry Trace Waterfall showing gen_ai.invoke_agent, gen_ai.chat, and gen_ai.execute_tool spans -->
<!-- Add screenshot here: ![Sentry Trace Waterfall](https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/sentry_trace.png) -->

---

## Benchmarks & Evaluation

To evaluate forensic reliability, we benchmarked the extraction pipeline across 58 historical snapshot attempts and evaluated fact-checking accuracy against hand-labeled ground truth.

### Benchmark 1: Extraction Yield — Browserbase vs. Raw HTTP

| Extraction Strategy | Total Attempts | Usable Yield % | Avg Characters Extracted | Avg Latency | p50 Latency | p95 Latency |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Raw HTTP (`id_/` endpoint)** | 31 | 100.0% | 964 chars | 10.3s | 3.3s | 36.7s |
| **Browserbase (CDP / DOM)** | 27 | 81.5% | 1,513 chars | 18.6s | 15.1s | 30.2s |

#### Key Findings:
- **Context Depth:** When Browserbase succeeds, it extracts **57% more text** (1,513 chars vs. 964 chars) by fully executing client-side JavaScript, hydration bundles, and retro Flash fallbacks.
- **Latency & Rate Limits:** Raw HTTP was faster for simple static HTML sites from the 90s. Browserbase’s 81.5% yield reflected free-plan concurrency ceilings and Archive.org replay timeouts rather than extraction failure.

<!-- Screenshot: Benchmark Page with Latency Distribution and Yield Graphs -->
<!-- Add screenshot here: ![Benchmark Page](https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/benchmark_charts.png) -->

---

### Benchmark 2: Fact-Checker Hallucination Elimination

We tested Gemma's self-correcting rewrite loop across 55 atomic factual assertions extracted from initial eulogies:

- **Total Claims Extracted:** 55
- **Ungrounded Claims Before Rewrite:** 21 (38.2%)
- **Ungrounded Claims After Rewrite:** 11 (20.0%)
- **Net Hallucination Reduction:** **47.6% of ungrounded assertions purged or corrected**

The fact-checker reliably caught hallucinated death dates, phantom corporate acquirers, and false technical claims, replacing them with honest admissions of archival silence.

---

### Benchmark 3: Canonical Cemetery Audit Table (15 Verified Seeds)

Every grave in the cemetery was audited directly from `graveyard.db`:

| Slug | Canonical Service | Lifeline | Recovered Chars | Cause in DB | Ground Truth Cause | Evidence Grounding |
|---|---|:---:|:---:|---|---|:---:|
| `google-reader` | Google Reader | 2005 – 2013 | 0 (clean) | `unknown` | `shut_down_by_owner` | Archive silent; honest `unknown` |
| `geocities` | GeoCities | 1995 – 2009 | 0 (clean) | `unknown` | `acquired_then_shut_down` | Archive silent; honest `unknown` |
| `vine` | Vine | 2013 – 2016 | 4 | `unknown` | `acquired_then_shut_down` | Thin evidence banner displayed |
| `grooveshark` | Grooveshark | 2007 – 2015 | 1,630 | `shut_down_by_owner` | `shut_down_by_owner` | **Ground truth match (1,630 chars)** |
| `flash` | Adobe Flash Player | 1996 – 2020 | 0 (clean) | `unknown` | `shut_down_by_owner` | Archive silent; honest `unknown` |
| `stumbleupon` | StumbleUpon | 2002 – 2018 | 0 (clean) | `unknown` | `shut_down_by_owner` | Replaced live MySpace; honest `unknown` |
| `yahoo-answers` | Yahoo Answers | 2005 – 2021 | 0 (clean) | `unknown` | `shut_down_by_owner` | Archive silent; honest `unknown` |
| `picnik` | Picnik | 2005 – 2012 | 237 | `acquired_then_shut_down` | `acquired_then_shut_down` | Real snippet match |
| `altavista` | AltaVista | 1996 – 2013 | 543 | `acquired_then_shut_down` | `acquired_then_shut_down` | Yahoo search redirect confirmed |
| `icq` | ICQ | 1997 – 2024 | 0 (clean) | `unknown` | `shut_down_by_owner` | Archive silent; honest `unknown` |
| `del-icio-us` | del.icio.us | 2003 – 2017 | 0 (clean) | `unknown` | `abandoned` | Verified dead (SSL/500 dead state) |
| `aim` | AOL Instant Messenger | 1997 – 2017 | 0 (clean) | `unknown` | `shut_down_by_owner` | Archive silent; honest `unknown` |
| `google-plus` | Google+ | 2011 – 2019 | 0 (clean) | `unknown` | `shut_down_by_owner` | Archive silent; honest `unknown` |
| `zune` | Microsoft Zune | 2006 – 2015 | 0 (clean) | `unknown` | `shut_down_by_owner` | Archive silent; honest `unknown` |
| `pebble` | Pebble | 2012 – 2016 | 1,595 | `acquired_then_shut_down` | `acquired_then_shut_down` | **Ground truth match (1,595 chars)** |

---

## Why Does Open Innovation Matter?

Why does open innovation matter for an autonomous digital historian?

1. **Unfiltered Historical Truth:** Proprietary AI systems are governed by changing safety filters, RLHF alignment drift, and commercial interests. An open-weights model like Gemma allows researchers to preserve web culture without a corporate parent deciding which dead competitors are remembered and which are quietly forgotten.
2. **Deterministic & Inspectable Pipelines:** In agentic workflows, reliability depends on transparent error handling. Running open-weights models gives developers direct control over temperature, context formatting, token limits, and Pydantic parsing without closed-source API black boxes dropping connections or injecting undocumented hidden system prompts.
3. **Preserving the Commons with Open Tools:** The Internet Archive is an open non-profit resource. Pairing open archival data with open-weights models and open observability standards ensures that digital archaeology remains accessible to everyone—not just well-funded tech conglomerates.

---

## My Agent Session

- **Autonomous Agent Session Trace:** Embedded via DevRelay / Sentry Trace ID
- **Artifact Dossier:** [Full Engineering Evidence Dossier & Ground Truth CSVs](https://github.com/Pritam-mb/week4/blob/main/EVIDENCE_DOSSIER.md)

---

## The Spirit of It

There is a moment when you exhume an old site—say, GeoCities in 1998, or Grooveshark with its vibrant beta announcement from 2007—and you realize that every paragraph, every animated gif, and every user quote was crafted by real people pouring their hearts into a fledgling medium. 

When software dies, it usually leaves no grave. Just an unfetchable DNS record and an expired SSL certificate. 

In our cemetery, when you click **"LEAVE A MARIGOLD"**, orange paper petals gently drift down your screen, incrementing an on-chain counter for that fallen tool. It isn't cynical or morbid; it is a celebration of what was built, a quiet acknowledgment that everything digital is impermanent, and a promise that the ghosts in our machines won't be forgotten.

<!-- Screenshot: Marigold Falling Petals Animation on a Grave Page -->
<!-- Add screenshot here: ![Marigold Animation](https://raw.githubusercontent.com/Pritam-mb/week4/main/static/screenshots/marigold_petals.png) -->

---

## Prize Categories

We are entering Graveyard of Dead Software into the following Hacktoberfest Week 4 categories:

- **Overall "Ghost in the Machine" Theme:** An end-to-end 5-stage agent that resurrects dead software from the archives of the web.
- **Gemma Category ($200):** Built from the ground up around Google’s open-weight `gemma-4-26b-a4b-it` model for forensic analysis, Día de los Muertos eulogy generation, and self-correcting fact-checking.
- **Render Category ($200):** Fully containerized web service deployed via [`render.yaml`](https://github.com/Pritam-mb/week4/blob/main/render.yaml) with automatic health probes, static assets caching, and persistent seed-bundle safeguards. *(Note: Render Free Tier instances use ephemeral storage; on paid plans with Persistent Disks, `graveyard.db` persists across restarts).*
- **Browserbase Category ($100):** Headless Chromium replay session recording, Stagehand DOM schema extraction, full-page screenshot generation, and a paired 58-attempt benchmark against raw HTTP.
- **Sentry Category ($100):** End-to-end OpenTelemetry GenAI agent tracing, tracking hierarchical `gen_ai.invoke_agent` → `gen_ai.chat` → `gen_ai.execute_tool` spans with token accounting and error handling.
- **.tech Domain Category ($100):** Ready for custom domain routing on `.tech`.

---

*Dedicated to Google Reader, Vine, GeoCities, and every other tool that gave us joy before the servers went dark.*
