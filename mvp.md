Here's the MVP plan regenerated as a clean markdown file. You can copy this into a file named `graveyard-mvp.md`.

```markdown
# Graveyard of Dead Software: MVP Plan

**Target prizes:** Gemma ($200), Render ($200), Browserbase ($100, go deep), free .tech domain ($100).  
Read the contest rules for Browserbase and .tech requirements before starting.

**Deadline:** submissions close Oct 31. Verify the exact time and timezone.

---

## One-line pitch

A public night-time cemetery of dead software and websites. An agent digs each one up from the Wayback Machine, Gemma writes its tombstone and eulogy, and visitors leave marigolds. Everything runs on open weights, so it can't end up in its own graveyard.

## Thesis (your blog's spine)

Every grave here died because someone closed it, abandoned it, or killed it.  
Open weights can't be shut off by a company.  
That one idea covers the theme, the "why open matters" question, and the emotional hook.

---

## MVP scope

### IN (must ship)

1. ~15 seeded graves, so the cemetery feels alive on day one.
2. The "dig up" pipeline: Wayback lookup → Browserbase fetch + screenshot → Gemma tombstone and eulogy.
3. Cemetery page (grid of tombstones at night) and a grave page.
4. Marigold counter per grave.
5. "Bury a project" form: a visitor submits a dead URL or name; the agent digs it up live.
6. Hosted on Render, with a .tech domain.

### OUT

- Accounts, comments, search
- GitHub archived-repo mining (stretch only)
- Fancy 3D or animation
- Perfect accuracy for every project (see disclaimer below)

---

## Pipeline

```
name or URL
    |
Wayback lookup  -> first snapshot (born), last good snapshot (last seen alive)
    |
Browserbase session -> open archived snapshot -> extract title + visible text + screenshot
    |
Gemma -> JSON: epitaph, eulogy, cause of death, survived by
    |
Save grave -> tombstone page on Render
```

---

## Step 1: Wayback lookup

Use the Wayback availability and CDX APIs (no key needed).  
Check current CDX docs for parameters, especially how to get the last snapshot.

```python
import requests

def first_snapshot(url):
    r = requests.get("https://web.archive.org/cdx/search/cdx",
                     params={"url": url, "output": "json", "limit": 1,
                             "filter": "statuscode:200", "fl": "timestamp,original"},
                     timeout=30).json()
    return r[1] if len(r) > 1 else None  # row 0 is the header

def last_snapshot(url):
    r = requests.get("https://web.archive.org/cdx/search/cdx",
                     params={"url": url, "output": "json", "limit": -1,  # verify negative limit
                             "filter": "statuscode:200", "fl": "timestamp,original"},
                     timeout=30).json()
    return r[-1] if len(r) > 1 else None

def archive_url(ts, original):
    return f"https://web.archive.org/web/{ts}/{original}"
```

Label dates honestly: "first archived" and "last seen alive in the archive". The last good capture is not necessarily the real death date.

---

## Step 2: Browserbase fetch (your "deep" sponsor)

Browserbase's Python SDK creates a remote browser session. Connect Playwright over CDP.  
Each session is recorded and viewable by session ID.

```python
from browserbase import Browserbase
from playwright.sync_api import sync_playwright
import os

bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

def exhume(archive_link):
    session = bb.sessions.create()
    replay = f"https://browserbase.com/sessions/{session.id}"
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session.connect_url)
        page = browser.contexts[0].pages[0]
        page.goto(archive_link, wait_until="domcontentloaded", timeout=45000)
        title = page.title()
        text = page.inner_text("body")[:6000]  # cap what you send to Gemma
        shot = page.screenshot(type="jpeg", quality=70)
        browser.close()
    return {"title": title, "text": text, "screenshot": shot, "replay": replay}
```

Install: `pip install browserbase playwright`.  
Put `BROWSERBASE_API_KEY` in env vars.

**Why this beats plain HTTP:** archived pages are messy (rewritten links, toolbar overlays, JS, redirects), and you want a real rendered screenshot for the tombstone. Be ready to explain that honestly in the post. Some pages could be fetched without a browser, so show where the browser actually helped.

### How to go deep on Browserbase

| Show | How |
|---|---|
| **Exhumation replays** | Save each session's replay link and put a "Watch the exhumation" link on every grave page |
| **Failure handling** | No snapshots, timeouts, blank pages, redirect loops, excluded pages. Handle each and say how |
| **Numbers** | Run all ~15 seeds + ~15 extra URLs. Report success rate, avg time per dig, and failure reasons in a table |
| **Findings** | What kinds of dead sites dig up cleanly vs badly (old Flash sites, JS-heavy apps, shut-down services with redirect pages) |
| **Debugging story** | One real failure with before/after. Likely candidates: `goto` timing out on slow snapshots (fix with `domcontentloaded` + a retry on an earlier/later snapshot), or extracted text being only an archive banner or "this site has moved" redirect page (fix by trying the next-closest snapshot). Also test the Wayback `id_` URL form (raw original content) for cleaner text |

---

## Step 3: Gemma

Run Gemma through whatever the contest allows (local Ollama, or an API).  
Send ONLY the facts you have: name, first/last archived dates, extracted text.

Prompt rules:

- Output JSON only: `epitaph` (one line), `eulogy` (80-120 words), `cause_of_death`, `survived_by`.
- Only state facts supported by extracted text or dates.
- Mark `cause_of_death` as "rumored" unless the page text says so.
- Warm and a little funny, written like a eulogy. If the page text is empty or useless, say "little is left of it."
- If the content is hateful, explicit, or unsafe, return `{"skip": true}`.

Parse with a JSON strip (remove code fences) and `try/except`; retry once on bad JSON.

---

## Step 4: App (Render)

- FastAPI + one HTML page (dark sky, tombstone cards, CSS only). Static assets are fine.
- Routes:
  - `GET /` (cemetery)
  - `GET /grave/{slug}`
  - `POST /marigold/{slug}`
  - `POST /bury` (submit a project, returns a job ID)
  - `GET /job/{id}` (poll progress: "searching the archive... exhuming... writing eulogy...")
- Seed graves: commit a `seed.json` with your ~15 pre-dug results, so the site works even if live digging fails.
- Storage: Render's free filesystem is not permanent. For marigold counts and user-submitted graves, use a Render Postgres database (check current pricing and free-tier limits) or accept that counts reset on redeploy for the demo.
- Protect the public form: per-IP rate limit, only `http/https` URLs, cap submissions per hour, since each dig uses a Browserbase session and Gemma call.
- Render settings: build `pip install -r requirements.txt`, start `uvicorn app:app --host 0.0.0.0 --port $PORT`. Free instances sleep when idle, so warm it up before the demo.
- .tech domain: claim it per the contest instructions and attach it as a custom domain in Render.

### Required disclaimer (put it on every grave)

> "Written by AI from archived pages. Details may be wrong."

Mark causes of death as rumored. You are writing about real companies and projects, so don't state unverified claims as fact.

---

## Seed ideas

Verify every date through Wayback; don't write them from memory.

Famous services and sites: a feed reader, a free web-hosting community, a short-video app, a social network, a messenger, a music service.  
Add 3-5 personal ones, for example a library you used in 2012 or your first favorite tool. Personal graves make the post more human.

---

## Timeline

| When | Task | Done when |
|---|---|---|
| Thu (today) | Wayback functions + Browserbase `exhume()` working on 5 URLs | 5 screenshots + text extracted |
| Thu night | Gemma prompt + JSON parsing, `seed.json` with 15 graves | 15 graves generated |
| Fri morning | FastAPI app, cemetery page, grave page, marigolds, deploy to Render | Public URL works |
| Fri afternoon | "Bury a project" live flow, rate limits, replay links, stats table, .tech domain | Live submission works |
| Fri night / Sat | Demo video, blog post, submit | Submitted before deadline |

**Gate:** by Thursday night, `exhume()` must work on at least 10 of your 15 seeds.  
If digging is too unreliable, show more graves from `seed.json` and treat the live form as a stretch.

---

## Cut list (in this order)

1. GitHub archived-repo graves
2. Marigold animations
3. Live "bury a project" polish (keep a simple version)
4. Never cut: seeded graves, Browserbase replays + stats table, the thesis in the post

---

## 90-second demo script

1. (15s) Dark cemetery loads, tombstones glow. "Everything here was killed by someone."
2. (30s) Submit a dead URL live. Progress messages appear, then a new grave.
3. (20s) Open a grave: screenshot, eulogy, "Watch the exhumation" replay.
4. (25s) Leave a marigold. Close: "This one runs on open weights. It can't die."

---

## Blog outline

- Hook: "The first tool I ever loved was ..." (use a real one).
- The idea: a cemetery for software.
- How digging works (diagram) and why a real browser was needed.
- Browserbase deep dive: replays, failure table, debugging story.
- Gemma: how to write a eulogy without making things up.
- Why open weights matter: the thesis.
- What I'd bury next.

---

## Submission checklist

- [ ] Rules checked for Browserbase and .tech requirements
- [ ] All dates verified through Wayback
- [ ] AI-written disclaimer on every grave
- [ ] Rate limit on the public form
- [ ] Stats table with real numbers and failure reasons
- [ ] Session replay links working
- [ ] Public repo, Render URL, .tech domain, demo video, blog post
```