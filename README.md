# Graveyard of Dead Software

> A digital cemetery for software the internet forgot. An agent exhumes a dead service from the Wayback Machine, determines cause of death from evidence, writes a eulogy with open-weight Gemma, and fact-checks itself before burial.

Hacktoberfest DEV Challenge — Week 4: "Ghost in the Machine"

---

## Architecture & 5-Stage Agentic Pipeline

```
POST /bury ──► jobs table ──► worker runs 5 stages, each persisted & resumable
                                   │
  1. Archaeologist  CDX API → lifeline sparkline, birth/peak/decline/last-alive snapshots
  2. Exhumer        Browserbase (Stagehand extract + screenshot) → HTTP id_ fallback
  3. Coroner        Deterministic signals + LLM forensic analysis → cause enum + [E#] cites
  4. Eulogist       Open-weight LLM → epitaph, eulogy, survived_by (must cite [E#])
  5. Fact-checker   Atomic claims extraction → verify vs evidence → rewrite loop (before/after)
                                   │
                         grave row status=done ──► /grave/<slug>
```

### Routes
| Route | Description |
|---|---|
| `GET /` | Cemetery grid with Día de los Muertos styling and stats |
| `GET /grave/<slug>` | Grave page with inline SVG lifeline sparkline, screenshot, replay link, cited eulogy, coroner verdict, fact-check claims, and visitor memories |
| `POST /bury` | Rate-limited (3/hr), runs the 5-stage exhumation pipeline |
| `GET /job/<id>` | Poll job progress and per-stage status |
| `POST /marigold/<slug>` | Leave ofrenda marigolds for a dead service |
| `POST /memory/<slug>` | Rate-limited (5/hr), max 500 chars, HTML-escaped memory book |
| `GET /benchmark` | Eval A: HTTP vs Browserbase extraction benchmark across eras |
| `GET /health` | Health check: DB connection and provider configuration (no secrets exposed) |

---

## Local Development Setup

1. **Clone & Virtual Environment:**
   ```bash
   git clone <repo-url>
   cd week4
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   # or source venv/bin/activate # Linux/macOS
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Copy `.env.example` to `.env` and configure:
   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=openai/gpt-oss-20b
   BROWSERBASE_API_KEY=your_browserbase_api_key
   SENTRY_DSN=your_sentry_dsn
   ```

3. **Database Initialization & Run:**
   ```bash
   uvicorn app:app --reload --port 8000
   ```
   Open `http://localhost:8000`.

---

## Deployment (Render)

The project includes `render.yaml` for 1-click deployment on Render.

> [!IMPORTANT]
> **Data Persistence Notice:**
> By default on Render free web services, the local SQLite database (`graveyard.db`) and saved screenshots reside on an ephemeral filesystem that resets on every deploy or restart.
> To persist user-submitted graves, memories, and benchmark results permanently across redeploys, attach a **Persistent Disk** on Render (e.g. mounted at `/var/data`) and set:
> `DATABASE_URL=sqlite+aiosqlite:////var/data/graveyard.db`

---

## Agent Session & Forensic Audit Log

This project was built pairing with **Google Antigravity** (Advanced Agentic AI Pair Programming) for the Hacktoberfest Open-Source AI Challenge: *Ghost in the Machine*.

- **Agent Session & Forensic Audit Dossier:** [`AUDIT_LOG.md`](AUDIT_LOG.md) *(mirrored at [`AGENT_SESSION.md`](AGENT_SESSION.md))*
- **Forensic Verification Script:** `python scripts/proof_pack.py` (reproduces all database metrics, 15-grave ground truth, error counts, and fact-checker statistics)
- **Unit Test Suite (20 tests):** `python -m unittest discover tests -v`

---

## Scripts

- `python scripts/proof_pack.py`: Reproducible audit script verifying the 15-grave ground truth matrix, crawl attempt distributions, and fact-checker audit math.
- `python seed_redig.py`: Idempotent and resumable re-digging of seed graves through the live exhumation pipeline. Pass `--force` to re-dig all graves.
- `python seed_bundle.py`: Creates a distributable ZIP bundle (`seed_bundle/seed_bundle.zip`) containing the database and screenshots.
- `python benchmark.py`: Runs Eval A benchmark (HTTP vs Browserbase) on 35 historical sites.
- `python scripts/metrics.py`: Prints markdown summary metrics tables for DEV post publication.
