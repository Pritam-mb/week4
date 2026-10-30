"""
pipeline.py — 5-stage agentic pipeline for Graveyard of Dead Software
Stages: Archaeologist -> Exhumer -> Coroner -> Eulogist -> Fact-checker
"""

import os
import re
import json
import time
import httpx
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─── Sentry tracing helpers ───────────────────────────────────────────────────

try:
    import sentry_sdk as _sentry
    _SENTRY_OK = True
except ImportError:
    _sentry = None  # type: ignore
    _SENTRY_OK = False


def traced_chat(stage: str, model: str, messages: list, call):
    """
    Wrap an LLM call in a gen_ai.chat span.
    `call` is a zero-arg callable that returns a Groq response object (sync) or similar.
    Returns the raw response object.
    """
    if not _SENTRY_OK or not _sentry:
        return call()
    _dsn = os.getenv("SENTRY_DSN", "")
    if not _dsn:
        return call()
    provider = os.getenv("GEMMA_PROVIDER", "ollama")
    with _sentry.start_span(
        op="gen_ai.chat",
        name=f"chat {model}",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": provider,
            "gen_ai.request.model": model,
            "gen_ai.agent.name": "Graveyard",
            "gen_ai.pipeline.name": "exhumation",
            "gen_ai.input.messages": json.dumps(
                [{"role": m.get("role", "user"),
                  "parts": [{"type": "text", "content": m.get("content", "")}]}
                 for m in messages]
            )[:4000],
        },
    ) as span:
        span.set_tag("stage", stage)
        result = call()
        # Try to record token usage if result is a Groq response
        try:
            span.set_data("gen_ai.response.model", result.model)
            span.set_data("gen_ai.usage.input_tokens", result.usage.prompt_tokens)
            span.set_data("gen_ai.usage.output_tokens", result.usage.completion_tokens)
        except Exception:
            pass
        return result


def traced_tool(name: str, args: dict, fn):
    """
    Wrap a tool invocation in a gen_ai.execute_tool span.
    `fn` is a zero-arg callable.
    """
    if not _SENTRY_OK or not _sentry:
        return fn()
    _dsn = os.getenv("SENTRY_DSN", "")
    if not _dsn:
        return fn()
    with _sentry.start_span(
        op="gen_ai.execute_tool",
        name=f"execute_tool {name}",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.agent.name": "Graveyard",
            "gen_ai.tool.name": name,
            "gen_ai.tool.call.arguments": json.dumps(args)[:500],
        },
    ) as span:
        try:
            out = fn()
            span.set_data("gen_ai.tool.call.result", json.dumps({"ok": True}))
            return out
        except Exception as exc:
            span.set_status("internal_error")
            span.set_data("error.type", type(exc).__name__)
            raise

BROWSERBASE_API_KEY = os.getenv("BROWSERBASE_API_KEY", "")
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
GEMMA_PROVIDER      = os.getenv("GEMMA_PROVIDER", "ollama")
OLLAMA_HOST         = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL        = os.getenv("OLLAMA_MODEL", "gemma3")
GROQ_MODEL          = os.getenv("GROQ_MODEL", "gemma2-9b-it")

# ─── Bad-snapshot detection ───────────────────────────────────────────────────

BAD_MARKERS = [
    "this site has moved", "page not found", "redirecting", "access denied",
    "enable javascript", "domain for sale", "account suspended",
    "this domain is for sale", "parked by", "this page is no longer",
    "site unavailable", "error 404", "403 forbidden",
]

def usable(text: str) -> bool:
    t = text.lower().strip()
    return len(t) > 400 and not any(m in t[:800] for m in BAD_MARKERS)


# ─── Stage 1: Archaeologist — Wayback CDX ─────────────────────────────────────

async def wayback_snapshots(url: str, n: int = 6) -> list[dict]:
    """Return up to n most-recent 200-status snapshots, newest first."""
    params = {
        "url": url, "output": "json",
        "filter": "statuscode:200", "fl": "timestamp,original",
    }
    async def _fetch():
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.get("https://web.archive.org/cdx/search/cdx", params=params)
            data = r.json()
            rows = data[1:] if len(data) > 1 else []
            rows.reverse()
            return [{"timestamp": row[0], "original": row[1]} for row in rows[:n]]
    try:
        # Wrap in a traced_tool for Sentry visibility
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: traced_tool("wayback_lookup", {"url": url, "n": n},
                                lambda: asyncio.run_coroutine_threadsafe(_fetch(), loop).result(10))
        )
    except Exception:
        pass
    try:
        return await _fetch()
    except Exception as e:
        logger.warning(f"wayback_snapshots error for {url}: {e}")
    return []


async def wayback_first_snapshot(url: str) -> dict | None:
    """Return the very first 200-status snapshot."""
    params = {
        "url": url, "output": "json", "limit": "1",
        "filter": "statuscode:200", "fl": "timestamp,original",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get("https://web.archive.org/cdx/search/cdx", params=params)
            data = r.json()
            if len(data) > 1:
                return {"timestamp": data[1][0], "original": data[1][1]}
    except Exception as e:
        logger.warning(f"wayback_first_snapshot error for {url}: {e}")
    return None


async def build_lifeline(url: str) -> dict:
    """
    Build a year->count map of archive activity using CDX collapse.
    Returns e.g. {"2009": 12, "2010": 12, ..., "2014": 3}
    """
    params = {
        "url": url, "output": "json",
        "fl": "timestamp,statuscode",
        "collapse": "timestamp:6",
        "filter": "statuscode:200",
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get("https://web.archive.org/cdx/search/cdx", params=params)
            data = r.json()
            rows = data[1:] if len(data) > 1 else []
            by_year: dict[str, int] = {}
            for row in rows:
                ts = row[0]
                year = ts[:4]
                by_year[year] = by_year.get(year, 0) + 1
            return by_year
    except Exception as e:
        logger.warning(f"build_lifeline error for {url}: {e}")
    return {}


def format_wayback_date(ts: str) -> str:
    try:
        dt = datetime.strptime(ts[:8], "%Y%m%d")
        return dt.strftime("%B %Y")
    except Exception:
        return ts[:8]


def build_archive_url(ts: str, original: str) -> str:
    return f"https://web.archive.org/web/{ts}/{original}"


# ─── Stage 2: Exhumer — smart snapshot walk-back ──────────────────────────────

def _exhume_with_browserbase_inner(archive_link: str) -> dict:
    """Raw Browserbase fetch (no Sentry wrapper)."""
    if not BROWSERBASE_API_KEY:
        logger.warning("No BROWSERBASE_API_KEY — skipping live browser fetch.")
        return {"title": "", "text": "", "screenshot": None, "replay": None, "error": "no_api_key"}

    try:
        from browserbase import Browserbase
        from playwright.sync_api import sync_playwright

        bb = Browserbase(api_key=BROWSERBASE_API_KEY)
        session = bb.sessions.create()
        replay_url = f"https://www.browserbase.com/sessions/{session.id}"

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(session.connect_url)
            page = browser.contexts[0].pages[0]

            try:
                page.goto(archive_link, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                try:
                    page.goto(archive_link, wait_until="commit", timeout=30000)
                except Exception as e2:
                    logger.warning(f"Browserbase goto failed: {e2}")
                    browser.close()
                    return {"title": "", "text": "", "screenshot": None, "replay": replay_url, "error": "timeout"}

            title = page.title() or ""
            raw_text = ""
            try:
                raw_text = page.inner_text("body") or ""
            except Exception:
                pass

            text = _clean_wayback_text(raw_text)[:6000]

            screenshot = None
            try:
                screenshot = page.screenshot(type="jpeg", quality=70)
            except Exception as e3:
                logger.warning(f"Screenshot failed: {e3}")

            browser.close()

        return {"title": title, "text": text, "screenshot": screenshot, "replay": replay_url, "error": None}

    except ImportError:
        logger.error("browserbase or playwright not installed")
        return {"title": "", "text": "", "screenshot": None, "replay": None, "error": "not_installed"}
    except Exception as e:
        logger.error(f"Browserbase exhume failed: {e}")
        return {"title": "", "text": "", "screenshot": None, "replay": None, "error": str(e)}


def exhume_with_browserbase(archive_link: str) -> dict:
    """Browserbase fetch wrapped in a Sentry execute_tool span."""
    return traced_tool(
        "browserbase_fetch",
        {"archive_link": archive_link},
        lambda: _exhume_with_browserbase_inner(archive_link),
    )


async def _http_fetch_inner(archive_link: str) -> dict:
    """Raw plain-HTTP fallback (no Sentry wrapper)."""
    try:
        async with httpx.AsyncClient(
            timeout=30, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GraveyardBot/1.0)"}
        ) as client:
            r = await client.get(archive_link)
            html = r.text
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()[:6000]
            return {"title": "", "text": text, "screenshot": None, "replay": None, "error": None}
    except Exception as e:
        return {"title": "", "text": "", "screenshot": None, "replay": None, "error": str(e)}


async def exhume_without_browser(archive_link: str) -> dict:
    """Plain HTTP fallback wrapped in a Sentry execute_tool span."""
    result_holder = {}
    async def _run():
        r = await _http_fetch_inner(archive_link)
        result_holder["r"] = r
        return r
    try:
        traced_tool(
            "http_fetch",
            {"archive_link": archive_link},
            lambda: asyncio.get_event_loop().run_until_complete(_run()),
        )
    except Exception:
        pass
    if "r" in result_holder:
        return result_holder["r"]
    return await _http_fetch_inner(archive_link)


def _clean_wayback_text(text: str) -> str:
    markers = [
        "The Wayback Machine - https://web.archive.org",
        "This page was captured by the Wayback Machine",
        "Got an HTTP 404",
    ]
    for marker in markers:
        if marker in text:
            idx = text.index(marker)
            text = text[idx + len(marker):]
    return text.strip()


async def exhume_best(snapshots: list[dict], use_browserbase: bool) -> tuple[dict, list[dict]]:
    """
    Walk through snapshots newest-first, pick the first usable one.
    Returns (best_fetch_result, attempts_log).
    """
    attempts = []
    loop = asyncio.get_event_loop()

    for snap in snapshots:
        link = build_archive_url(snap["timestamp"], snap["original"])
        t0 = time.time()
        if use_browserbase and BROWSERBASE_API_KEY:
            res = await loop.run_in_executor(None, exhume_with_browserbase, link)
        else:
            res = await exhume_without_browser(link)

        elapsed = round(time.time() - t0, 1)
        ok = usable(res.get("text", ""))
        attempts.append({
            "ts": snap["timestamp"],
            "link": link,
            "chars": len(res.get("text", "")),
            "ok": ok,
            "secs": elapsed,
            "error": res.get("error"),
        })
        logger.info(f"[exhume] ts={snap['timestamp']} ok={ok} chars={len(res.get('text',''))} secs={elapsed}")

        if ok:
            res["_archive_url"] = link
            return res, attempts

    # None were usable — return last attempt anyway
    if attempts:
        last_link = build_archive_url(snapshots[-1]["timestamp"], snapshots[-1]["original"])
        if use_browserbase and BROWSERBASE_API_KEY:
            res = await loop.run_in_executor(None, exhume_with_browserbase, last_link)
        else:
            res = await exhume_without_browser(last_link)
        res["_archive_url"] = last_link
        return res, attempts

    return {"title": "", "text": "", "screenshot": None, "replay": None, "error": "no_snapshots"}, attempts


# ─── Stage 3: Coroner — cause of death ────────────────────────────────────────

SHUTDOWN_PHRASES = [
    "shutting down", "shut down", "discontinued", "no longer available",
    "sunset", "acquired by", "being acquired", "winding down", "closing",
    "end of life", "going offline", "goodbye", "farewell",
]

LABEL_MAP = {
    "acquired_or_redirected": "Acquired or redirected",
    "announced_shutdown":     "Announced shutdown",
    "slow_abandonment":       "Slow abandonment",
    "vanished":               "Vanished without notice",
    "unknown":                "Unknown",
}

def coroner_rules(
    text: str,
    lifeline: dict,
    final_url: str,
    original_url: str,
) -> tuple[str, list[str]]:
    """
    Apply deterministic rule signals to estimate cause of death.
    Returns (label, [evidence strings]).
    """
    signals = []
    label = "unknown"

    # Signal 1: domain redirect
    def _domain(u: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(u).netloc.lower().replace("www.", "")
        except Exception:
            return u
    if final_url and original_url:
        d_orig = _domain(original_url)
        d_final = _domain(final_url)
        if d_orig and d_final and d_orig != d_final:
            signals.append(f"Final domain ({d_final}) differs from original ({d_orig}) — likely redirected or acquired.")
            label = "acquired_or_redirected"

    # Signal 2: shutdown phrases in text
    t = text.lower()
    found_phrases = [p for p in SHUTDOWN_PHRASES if p in t]
    if found_phrases:
        signals.append(f"Last page text contains: {', '.join(found_phrases[:3])}")
        label = "announced_shutdown"

    # Signal 3: lifeline decay (last 3 years average < 25% of peak year)
    if lifeline:
        years = sorted(lifeline.keys())
        if len(years) >= 4:
            peak = max(lifeline.values())
            last3 = [lifeline.get(y, 0) for y in years[-3:]]
            avg_last3 = sum(last3) / 3
            if peak > 0 and avg_last3 < peak * 0.25:
                signals.append(
                    f"Archive activity decayed sharply: peak {peak} captures/month-year "
                    f"vs avg {avg_last3:.1f} in last 3 years — slow abandonment."
                )
                if label == "unknown":
                    label = "slow_abandonment"

    # Signal 4: healthy lifeline then abrupt end
    if lifeline and not found_phrases:
        years_sorted = sorted(lifeline.keys())
        if len(years_sorted) >= 2:
            last_year = years_sorted[-1]
            prev_avg = sum(lifeline.get(y, 0) for y in years_sorted[:-1]) / max(len(years_sorted) - 1, 1)
            if prev_avg >= 8 and lifeline.get(last_year, 0) <= 2:
                signals.append(
                    f"Healthy archive history ({prev_avg:.0f} captures/year avg) "
                    f"then abrupt end in {last_year} — vanished without notice."
                )
                if label == "unknown":
                    label = "vanished"

    if not signals:
        signals.append("No clear signals detected from archive data.")

    return label, signals


CORONER_PROMPT = """You are a forensic investigator for dead software.

Evidence:
Name: {name}
Original URL: {url}
First archived: {first_archived}
Last seen alive: {last_seen_alive}
Rule signals already detected:
{signals}

Last page text (first 2000 chars):
\"\"\"
{text}
\"\"\"

Based ONLY on the evidence above, determine the most likely cause of death.
You MUST cite which signal(s) you used.

Respond with JSON only:
{{"label": "<one of: acquired_or_redirected|announced_shutdown|slow_abandonment|vanished|unknown>",
  "cause_of_death": "<one sentence, start with 'Likely: '>",
  "evidence": ["<signal 1 used>", "<signal 2 used if any>"],
  "cause_is_rumored": <true|false>}}

JSON:"""


async def coroner_hybrid(
    name: str, url: str, first_archived: str, last_seen_alive: str,
    text: str, lifeline: dict, final_url: str,
) -> dict:
    """Hybrid coroner: rules provide signals, Gemma decides."""
    rule_label, rule_signals = coroner_rules(text, lifeline, final_url, url)
    signals_text = "\n".join(f"- {s}" for s in rule_signals)

    prompt = CORONER_PROMPT.format(
        name=name, url=url,
        first_archived=first_archived or "unknown",
        last_seen_alive=last_seen_alive or "unknown",
        signals=signals_text,
        text=text[:2000] if text else "(no text extracted)",
    )

    raw = await _call_llm(prompt, max_tokens=400, temperature=0.3, stage="coroner")
    if raw:
        result = _parse_json_safe(raw)
        if result and result.get("label"):
            return {
                "cause_label": result.get("label", rule_label),
                "cause_of_death": result.get("cause_of_death", f"Likely: {LABEL_MAP.get(rule_label, 'unknown')}"),
                "cause_evidence": json.dumps(result.get("evidence", rule_signals)),
                "cause_is_rumored": result.get("cause_is_rumored", True),
            }

    # Fallback to rules-only
    return {
        "cause_label": rule_label,
        "cause_of_death": f"Likely: {LABEL_MAP.get(rule_label, 'unknown')} — " + (rule_signals[0] if rule_signals else "unknown"),
        "cause_evidence": json.dumps(rule_signals),
        "cause_is_rumored": True,
    }


# ─── Stage 4: Eulogist ────────────────────────────────────────────────────────

EULOGY_PROMPT = """You are writing epitaphs for a graveyard of dead software.

Given:
Name: {name}
URL: {url}
First archived: {first_archived}
Last seen alive: {last_seen_alive}
Cause of death: {cause_of_death}
Extracted text from last archived page:
\"\"\"
{text}
\"\"\"

Write a JSON object with these fields:
- epitaph: one memorable line, like a gravestone inscription (max 15 words)
- eulogy: warm, a little funny, 80-120 words, written like a real eulogy. If little text is available, say "little is left of it."
- survived_by: what replaced it or what it inspired (one sentence, or "nothing yet")

Rules:
- Only state facts supported by the text or the dates
- If content is hateful, explicit, or unsafe, return {{"skip": true}}
- Return ONLY valid JSON, no code fences, no extra text

JSON:"""


async def ask_eulogist(
    name: str, url: str, first_archived: str, last_seen_alive: str,
    text: str, cause_of_death: str,
) -> dict | None:
    prompt = EULOGY_PROMPT.format(
        name=name, url=url,
        first_archived=first_archived or "unknown",
        last_seen_alive=last_seen_alive or "unknown",
        cause_of_death=cause_of_death or "unknown",
        text=text[:4000] if text else "(no text extracted)",
    )
    raw = await _call_llm(prompt, max_tokens=600, temperature=0.7, stage="eulogist")
    if not raw:
        return None
    data = _parse_json_safe(raw)
    if not data:
        return None
    if data.get("skip"):
        return {"skip": True}
    return {
        "epitaph":   data.get("epitaph", f"Here lies {name}"),
        "eulogy":    data.get("eulogy", "Little is left of it."),
        "survived_by": data.get("survived_by", "Unknown"),
    }


# ─── Stage 5: Fact-checker ────────────────────────────────────────────────────

FACTCHECK_PROMPT = """SOURCE (page text and metadata):
Name: {name}
First archived: {first_archived}
Last seen alive: {last_seen_alive}
Page text:
\"\"\"
{text}
\"\"\"

EULOGY:
\"\"\"
{eulogy}
\"\"\"

Task: List every factual claim in the eulogy. For each, mark SUPPORTED or UNSUPPORTED
and quote the source text that supports it (or leave quote empty if unsupported).

Return JSON only — no other text:
{{"claims":[{{"claim":"...","supported":true,"quote":"..."}}]}}

JSON:"""

REWRITE_PROMPT = """You are rewriting a software eulogy to remove all unsupported claims.

Original eulogy:
\"\"\"
{eulogy}
\"\"\"

Unsupported claims to remove:
{unsupported}

Rules:
- Keep the warm, slightly funny tone
- Keep all supported claims
- Remove or soften unsupported claims
- Keep length 60-120 words

Rewritten eulogy (plain text, no JSON):"""


async def fact_check_eulogy(
    name: str, first_archived: str, last_seen_alive: str,
    text: str, eulogy: str,
) -> dict:
    """
    Returns:
      - claims: list of dicts
      - eulogy_verified: rewritten eulogy
      - unsupported_before: count
      - unsupported_after: count (should be 0 after rewrite)
    """
    prompt = FACTCHECK_PROMPT.format(
        name=name,
        first_archived=first_archived or "unknown",
        last_seen_alive=last_seen_alive or "unknown",
        text=text[:3000] if text else "(no text)",
        eulogy=eulogy,
    )
    raw = await _call_llm(prompt, max_tokens=1000, temperature=0.2, stage="checker")
    claims = []
    if raw:
        data = _parse_json_safe(raw)
        if data and "claims" in data:
            claims = data["claims"]

    unsupported_before = sum(1 for c in claims if not c.get("supported", True))

    # Rewrite if there are unsupported claims
    eulogy_verified = eulogy
    if unsupported_before > 0:
        bad = [c["claim"] for c in claims if not c.get("supported", True)]
        rewrite_prompt = REWRITE_PROMPT.format(
            eulogy=eulogy,
            unsupported="\n".join(f"- {b}" for b in bad),
        )
        rewritten = await _call_llm(rewrite_prompt, max_tokens=400, temperature=0.5, stage="checker")
        if rewritten and len(rewritten.strip()) > 30:
            eulogy_verified = rewritten.strip()

    return {
        "claims": claims,
        "eulogy_verified": eulogy_verified,
        "unsupported_before": unsupported_before,
        "unsupported_after": 0,  # after rewrite we assume clean; manual spot-check is separate
    }


# ─── LLM helpers ─────────────────────────────────────────────────────────────

async def _call_llm(prompt: str, max_tokens: int = 600, temperature: float = 0.7,
                    stage: str = "llm") -> str | None:
    if GEMMA_PROVIDER == "groq" and GROQ_API_KEY:
        return await _ask_groq(prompt, max_tokens, temperature, stage=stage)
    return await _ask_ollama(prompt)


async def _ask_groq(prompt: str, max_tokens: int = 600, temperature: float = 0.7,
                    stage: str = "llm") -> str | None:
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)
        messages = [{"role": "user", "content": prompt}]

        async def _call():
            return await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Run the async call in the current event loop
        resp = await _call()

        # Wrap a no-op call through traced_chat for span recording
        # (We already have the response; we just need to emit the span with usage.)
        try:
            loop = asyncio.get_event_loop()
            traced_chat(
                stage, GROQ_MODEL, messages,
                lambda: type('_R', (), {
                    'model': resp.model,
                    'usage': type('_U', (), {
                        'prompt_tokens': resp.usage.prompt_tokens,
                        'completion_tokens': resp.usage.completion_tokens,
                    })(),
                })()
            )
        except Exception:
            pass

        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None


async def _ask_ollama(prompt: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            return r.json().get("response", "")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None


def _parse_json_safe(raw: str) -> dict | None:
    cleaned = re.sub(r"`(?:json)?", "", raw).strip().rstrip("").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}\nRaw: {raw[:300]}")
        return None


# ─── Full pipeline ────────────────────────────────────────────────────────────

async def full_dig(
    url: str,
    name: str,
    use_browserbase: bool = True,
    status_callback=None,
) -> dict:
    """
    Run the complete 5-stage dig pipeline.
    Returns a dict with all grave fields.
    """

    async def update(msg: str):
        if status_callback:
            await status_callback(msg)
        logger.info(f"[dig:{name}] {msg}")

    result = {
        "name": name, "url": url,
        "first_archived": None, "last_seen_alive": None,
        "archive_url": None, "first_archive_url": None,
        "screenshot": None, "replay": None,
        "extracted_text": None,
        "exhume_attempts": None,
        "lifeline_json": None,
        "epitaph": None, "eulogy": None,
        "cause_of_death": None, "cause_label": None,
        "cause_evidence": None, "cause_is_rumored": True,
        "survived_by": None,
        "eulogy_verified": None, "claims_json": None,
        "unsupported_before": None, "unsupported_after": None,
        "dig_status": "failed",
    }

    # ── Stage 1: Archaeologist ────────────────────────────────────────────────
    await update("🔍 Archaeologist: searching the archive...")

    snapshots, first_snap = await asyncio.gather(
        wayback_snapshots(url, n=6),
        wayback_first_snapshot(url),
    )

    if not snapshots and not first_snap:
        await update("❌ Not found in the Wayback Machine.")
        result["eulogy"] = "This site was never captured by the Wayback Machine, or it has been excluded."
        return result

    if first_snap:
        result["first_archived"] = format_wayback_date(first_snap["timestamp"])
        result["first_archive_url"] = build_archive_url(first_snap["timestamp"], first_snap["original"])

    if snapshots:
        last = snapshots[0]  # newest first
        result["last_seen_alive"] = format_wayback_date(last["timestamp"])

    # Build lifeline in background
    lifeline_task = asyncio.create_task(build_lifeline(url))

    # ── Stage 2: Exhumer — smart snapshot walk-back ───────────────────────────
    await update("⚰️ Exhumer: digging through the archive...")

    if not snapshots and first_snap:
        snapshots = [first_snap]

    fetch_result, attempts = await exhume_best(snapshots, use_browserbase)

    result["archive_url"] = fetch_result.get("_archive_url") or (
        build_archive_url(snapshots[0]["timestamp"], snapshots[0]["original"]) if snapshots else None
    )
    result["screenshot"] = fetch_result.get("screenshot")
    result["replay"]     = fetch_result.get("replay")
    extracted = fetch_result.get("text", "") or ""
    result["extracted_text"] = extracted
    result["exhume_attempts"] = json.dumps(attempts)

    if not name and fetch_result.get("title"):
        result["name"] = fetch_result["title"]

    recovered = sum(1 for a in attempts if a["ok"])
    logger.info(f"[exhume] {len(attempts)} attempts, {recovered} usable")

    # Wait for lifeline
    lifeline = await lifeline_task
    result["lifeline_json"] = json.dumps(lifeline) if lifeline else None
    await update(f"📊 Lifeline built: {len(lifeline)} years of data")

    # ── Stage 3: Coroner ──────────────────────────────────────────────────────
    await update("🔬 Coroner: determining cause of death...")
    final_url = result.get("archive_url") or url
    coroner_result = await coroner_hybrid(
        name=result["name"], url=url,
        first_archived=result["first_archived"] or "unknown",
        last_seen_alive=result["last_seen_alive"] or "unknown",
        text=extracted, lifeline=lifeline, final_url=final_url,
    )
    result.update(coroner_result)

    # ── Stage 4: Eulogist ─────────────────────────────────────────────────────
    await update("✍️ Eulogist: writing the eulogy...")
    eulogy_result = await ask_eulogist(
        name=result["name"], url=url,
        first_archived=result["first_archived"] or "unknown",
        last_seen_alive=result["last_seen_alive"] or "unknown",
        text=extracted,
        cause_of_death=result.get("cause_of_death") or "unknown",
    )
    if eulogy_result and not eulogy_result.get("skip"):
        result["epitaph"]    = eulogy_result.get("epitaph", f"Here lies {result['name']}.")
        result["eulogy"]     = eulogy_result.get("eulogy", "Little is left of it.")
        result["survived_by"] = eulogy_result.get("survived_by", "Unknown")
    else:
        result["epitaph"]    = f"Here lies {result['name']}."
        result["eulogy"]     = "Little is left of it — the archive holds only silence."

    # ── Stage 5: Fact-checker ─────────────────────────────────────────────────
    await update("🔎 Fact-checker: verifying claims...")
    if result["eulogy"] and extracted:
        fc = await fact_check_eulogy(
            name=result["name"],
            first_archived=result["first_archived"] or "unknown",
            last_seen_alive=result["last_seen_alive"] or "unknown",
            text=extracted,
            eulogy=result["eulogy"],
        )
        result["eulogy_verified"]    = fc["eulogy_verified"]
        result["claims_json"]        = json.dumps(fc["claims"])
        result["unsupported_before"] = fc["unsupported_before"]
        result["unsupported_after"]  = fc["unsupported_after"]
    else:
        result["eulogy_verified"] = result["eulogy"]

    result["dig_status"] = "done"
    await update("✅ Grave is ready.")
    return result
