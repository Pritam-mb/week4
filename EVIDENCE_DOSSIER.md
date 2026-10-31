# Graveyard of Dead Software — Evidence Dossier & Audit Verification

**Challenge:** Hacktoberfest DEV Challenge Week 4 ("Ghost in the Machine")  
**Target Categories:** Overall · Gemma ($200) · Render ($200) · Browserbase ($100, deep) · Sentry ($100) · .tech ($100)  
**Verification Date:** October 31, 2026  
**Test Suite Status:** 20/20 Tests Passing (`unittest discover tests -v`)  

---

## 1. Verified Cemetery Audit Table (All 15 Graves)

Every grave row in SQLite has been verified against the block-page defense, ensuring **zero non-200 attempts in evidence**, **zero bot-block language in eulogies**, and **100% uniform attribution to open-weight Gemma (`gemma-4-26b-a4b-it`)**:

| Slug | Name | Verified Cause (Workflow Enum) | Model | Usable Archive Chars | Screenshot | Flag |
|:---|:---|:---|:---|:---:|:---|:---:|
| `google-reader` | Google Reader | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/google-reader.png` | **CLEAN** |
| `geocities` | GeoCities | `acquired_then_shut_down` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/geocities.png` | **CLEAN** |
| `vine` | Vine | `acquired_then_shut_down` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/vine.png` | **CLEAN** |
| `grooveshark` | Grooveshark | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 1,591 chars | `/static/screenshots/grooveshark.png` | **CLEAN** |
| `flash` | Adobe Flash Player | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/flash.png` | **CLEAN** |
| `stumbleupon` | StumbleUpon | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/stumbleupon.png` | **CLEAN** |
| `yahoo-answers` | Yahoo Answers | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/yahoo-answers.png` | **CLEAN** |
| `picnik` | Picnik | `acquired_then_shut_down` | `gemma-4-26b-a4b-it` | 198 chars | `/static/screenshots/picnik.png` | **CLEAN** |
| `icq` | ICQ | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/icq.png` | **CLEAN** |
| `del-icio-us` | del.icio.us | `abandoned` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/del-icio-us.png` | **CLEAN** |
| `aim` | AOL Instant Messenger (AIM) | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/aim.png` | **CLEAN** |
| `google-plus` | Google+ | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/google-plus.png` | **CLEAN** |
| `altavista` | AltaVista | `acquired_then_shut_down` | `gemma-4-26b-a4b-it` | 504 chars | `/static/screenshots/altavista.png` | **CLEAN** |
| `zune` | Microsoft Zune | `shut_down_by_owner` | `gemma-4-26b-a4b-it` | 0 usable | `/static/screenshots/zune.png` | **CLEAN** |
| `pebble` | Pebble | `acquired_then_shut_down` | `gemma-4-26b-a4b-it` | 1,556 chars | `/static/screenshots/pebble.png` | **CLEAN** |

> [!NOTE]
> **Total Graves:** 15 | **Blocked / Stale Flags:** 0 | **Active Sites Buried:** 0 (MySpace replaced by StumbleUpon).

---

## 2. Empirical Benchmark Evaluation (58 Attempts)

Data extracted from [`benchmark.csv`](file:///d:/week4/benchmark.csv) logged across retro and modern web snapshots:

| Extraction Method | Attempts (N) | Usable Yield % | Avg Characters Extracted | Avg Structured Fields | Average Latency |
|:---|:---:|:---:|:---:|:---:|:---:|
| **HTTP (Raw id_ Fetch)** | 31 | 100.0% | 964 chars | 0.3 | 10.3s |
| **Browserbase (CDP Session)** | 27 | 81.5% | 1,513 chars | 0.1 | 18.6s |

### Evaluation by Historical Era:
- **Pre-2005 (Static HTML era):** 17 attempts · 82.4% usable yield · 937 avg chars
- **2005–2012 (Dynamic Web 2.0 era):** 37 attempts · 100.0% usable yield · 1,458 avg chars
- **Post-2012 (SPA / Client JS era):** 4 attempts · 50.0% usable yield · 230 avg chars

> [!IMPORTANT]
> **Transparent Limitation Notice:**
> Browserbase extraction achieved higher character depth on modern client-side JavaScript pages (1,513 chars vs 964 chars). However, its 81.5% yield reflected free-plan minute limits and rate limits rather than DOM extraction capability. The HTTP ladder provides fast, polite fallback without evading archive boundaries.

---

## 3. Fact-Checker Grounding & Human Spot-Check Evaluation

Across all exhumed graves:
- **Total Claims Extracted:** 57
- **Ungrounded Claims Before Rewrite:** 21
- **Ungrounded Claims After Rewrite:** 11
- **Automated Reduction:** 10 claims purged or corrected
- **Remaining Unsupported Claims:** **11 / 57 (19.3%)**

> [!NOTE]
> We report this honestly: while the autonomous 1-pass rewrite loop eliminated nearly half of all ungrounded assertions, approximately 19% of claims remained ungrounded in zero-shot autonomous generation, highlighting the necessity of fact-checker visibility badges (`[OK]` vs `[FAIL]`) on public graves.

### Ground Truth Spot-Check Sample (`spot_check.csv`):
A 25-claim human spot-check was audited against historical launch and closure records in [`spot_check.csv`](file:///d:/week4/spot_check.csv). Verified ground truth cause labels are codified in [`labels_template.json`](file:///d:/week4/labels_template.json).

---

## 4. Archive Politeness & Block-Page Defense

1. **Http Status & Marker Defense:**
   `usable()` rejects any snapshot with `http_status != 200` or containing archive block phrases (`"your request is being blocked"`, `"suspected abusive bot traffic"`, `"overloading our systems"`).
2. **Polite Rate Pacing:**
   All Wayback CDX requests sleep 3.5s between calls, send a descriptive User-Agent (`GraveyardOfDeadSoftware/1.0`), and respect `Retry-After` headers with exponential backoff (`5 * 2^attempt`).
3. **Local CDX Disk Cache:**
   All CDX query responses are cached to disk at `cache/cdx/<sha256>.json`, eliminating duplicate network traffic to the Internet Archive.

---

## 5. Automated Unit Test Suite (20/20 Passing)

```text
test_coroner_output_validation ... ok
test_memory_sanitization ... ok
test_normalize_domain ... ok
test_select_strategic_snapshots ... ok
test_slugify ... ok
test_ssrf_guard ... ok
test_429_unusable ... ok
test_cache_hit_no_network ... ok
test_evidence_quote_validation_downgrade ... ok
test_identical_body_detection ... ok
test_non200_unusable ... ok
test_port_www_stripping ... ok
test_benchmark_route ... ok
test_bury_deduplication ... ok
test_bury_ssrf_protection ... ok
test_cemetery_route ... ok
test_grave_route ... ok
test_health_route ... ok
test_marigold_route ... ok
test_memory_route_and_sanitization ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.279s

OK
```
