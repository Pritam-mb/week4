"""
app.py — Graveyard of Dead Software
FastAPI application with Sentry tracing, rate limiting, and all routes.
"""

import os
import json
import re
import uuid
import asyncio
import logging
import html as html_lib
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# ── Sentry: init FIRST, before anything that could auto-instrument ────────────
import sentry_sdk

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        data_collection={"gen_ai": {"inputs": True, "outputs": True}},
    )

# ── FastAPI & friends ─────────────────────────────────────────────────────────
from fastapi import FastAPI, Request, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import init_db, get_db, Grave, DigJob, BenchmarkResult, AsyncSessionLocal
from pipeline import full_dig, is_ssrf_safe, LLM_PROVIDER

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── App setup ─────────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Graveyard of Dead Software", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["fromjson"] = lambda s: json.loads(s) if (isinstance(s, str) and s.strip().startswith(("[", "{"))) else (s or [])

SCREENSHOTS_DIR = BASE_DIR / "static" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup():
    # Unpack seed bundle on clean deployment if needed
    db_file = BASE_DIR / "graveyard.db"
    bundle_zip = BASE_DIR / "seed_bundle" / "seed_bundle.zip"
    if (not db_file.exists() or db_file.stat().st_size == 0) and bundle_zip.exists():
        logger.info("Clean deployment detected: unpacking seed_bundle.zip...")
        import zipfile
        import shutil
        tmp_extract = BASE_DIR / "seed_bundle_tmp"
        try:
            with zipfile.ZipFile(bundle_zip, "r") as z:
                z.extractall(tmp_extract)
            tmp_db = tmp_extract / "graveyard.db"
            if tmp_db.exists():
                shutil.copy2(tmp_db, db_file)
            tmp_screens = tmp_extract / "screenshots"
            if tmp_screens.exists():
                for img in tmp_screens.glob("*"):
                    shutil.copy2(img, SCREENSHOTS_DIR / img.name)
            logger.info("Seed bundle unpacked successfully")
        except Exception as e:
            logger.warning(f"Failed to unpack seed bundle: {e}")
        finally:
            shutil.rmtree(tmp_extract, ignore_errors=True)

    await init_db()
    logger.info("Database initialized")
    # Resume any incomplete jobs on startup
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DigJob).where(DigJob.status.in_(["pending", "running"]))
            )
            incomplete = result.scalars().all()
            for job in incomplete:
                logger.info(f"Resuming dig job {job.id} for {job.url} from stage: {job.stage or 'archaeologist'}")
                use_bb = bool(os.getenv("BROWSERBASE_API_KEY"))
                asyncio.create_task(run_dig_job(job.id, job.url, "", use_bb))
    except Exception as e:
        logger.warning(f"Failed to check/resume jobs on startup: {e}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_domain(u: str) -> str:
    clean = (u or "").strip().lower()
    clean = re.sub(r"^https?://", "", clean)
    clean = re.sub(r"^www\.", "", clean)
    return clean.rstrip("/")


def slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s[:120] or "unknown"


def make_slug(name: str, url: str) -> str:
    base = slugify(name) if name else slugify(url.split("//")[-1].split("/")[0])
    return base or "grave"


async def save_screenshot(data: bytes, slug: str) -> str | None:
    if not data:
        return None
    try:
        path = SCREENSHOTS_DIR / f"{slug}.jpg"
        path.write_bytes(data)
        return f"/static/screenshots/{slug}.jpg"
    except Exception as e:
        logger.warning(f"Screenshot save failed: {e}")
        return None


async def grave_from_result(result: dict, db: AsyncSession, name: str, url: str) -> Grave:
    slug_base = make_slug(name or result.get("name", ""), url)
    slug = slug_base
    counter = 1
    while True:
        existing = await db.execute(select(Grave).where(Grave.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{slug_base}-{counter}"
        counter += 1

    # screenshot already saved to static/screenshots/<slug>.png by pipeline; use path directly
    screenshot_path = result.get("screenshot")

    grave = Grave(
        slug=slug,
        name=result.get("name") or name or url,
        url=url,
        first_archived=result.get("first_archived"),
        last_seen_alive=result.get("last_seen_alive"),
        archive_url=result.get("archive_url"),
        first_archive_url=result.get("first_archive_url"),
        lifeline_json=result.get("lifeline_json"),
        screenshot_path=screenshot_path,
        replay_url=result.get("replay"),
        extracted_text=result.get("extracted_text"),
        extracted_fields_json=json.dumps(result.get("extracted_fields")) if result.get("extracted_fields") else None,
        exhume_attempts=result.get("exhume_attempts"),
        epitaph=result.get("epitaph"),
        eulogy=result.get("eulogy"),
        cause_of_death=result.get("cause_of_death"),
        cause_label=result.get("cause_label"),
        cause_evidence=result.get("cause_evidence"),
        cause_is_rumored=result.get("cause_is_rumored", True),
        survived_by=result.get("survived_by"),
        eulogy_verified=result.get("eulogy_verified"),
        claims_json=result.get("claims_json"),
        unsupported_before=result.get("unsupported_before"),
        unsupported_after=result.get("unsupported_after"),
        dig_status=result.get("dig_status", "done"),
        llm_provider=result.get("llm_provider"),
        llm_model=result.get("llm_model"),
        is_seed=False,
    )
    db.add(grave)
    await db.commit()
    await db.refresh(grave)
    return grave


# ── Background dig job ────────────────────────────────────────────────────────

async def run_dig_job(job_id: str, url: str, name: str, use_browserbase: bool = True):
    """Run the 5-stage pipeline inside a Sentry gen_ai.invoke_agent root span."""
    import sentry_sdk

    async with AsyncSessionLocal() as db:
        j = await db.get(DigJob, job_id)
        if not j:
            return
        j.status = "running"
        j.message = "Starting dig..."
        j.stage = "archaeologist"
        await db.commit()

    # Set Sentry AI conversation ID
    if SENTRY_DSN:
        try:
            import sentry_sdk.ai
            sentry_sdk.ai.set_conversation_id(job_id)
        except Exception:
            pass

    async def update_job(msg: str):
        async with AsyncSessionLocal() as db:
            j = await db.get(DigJob, job_id)
            if j:
                j.message = msg
                # Track current stage from message prefix
                if msg.startswith("🔍"):
                    j.stage = "archaeologist"
                elif msg.startswith("⚰️"):
                    j.stage = "exhumer"
                elif msg.startswith("🔬"):
                    j.stage = "coroner"
                elif msg.startswith("✍️"):
                    j.stage = "eulogist"
                elif msg.startswith("🔎"):
                    j.stage = "fact_checker"
                elif msg.startswith("✅"):
                    j.stage = "done"
                await db.commit()

    async def _do_dig():
        return await full_dig(url, name, use_browserbase=use_browserbase,
                              status_callback=update_job)

    try:
        # 180s per-dig timeout
        if SENTRY_DSN:
            with sentry_sdk.start_span(
                op="gen_ai.invoke_agent",
                name="invoke_agent Graveyard",
                attributes={
                    "gen_ai.operation.name": "invoke_agent",
                    "gen_ai.agent.name": "Graveyard",
                    "gen_ai.pipeline.name": "exhumation",
                },
            ) as root_span:
                root_span.set_tag("job_id", job_id)
                root_span.set_tag("extractor", "browserbase" if use_browserbase else "http")
                root_span.set_tag("provider", LLM_PROVIDER)
                root_span.set_tag("exhume_method", "browserbase" if use_browserbase else "http")
                result = await asyncio.wait_for(_do_dig(), timeout=180)
                attempts = json.loads(result.get("exhume_attempts") or "[]")
                root_span.set_tag("walkback_count", max(0, len(attempts) - 1))
                root_span.set_tag("cause_label", result.get("cause_label") or "unknown")
                root_span.set_tag("cause", result.get("cause_label") or "unknown")
                root_span.set_tag("seed", "false")
        else:
            result = await asyncio.wait_for(_do_dig(), timeout=180)

        async with AsyncSessionLocal() as db:
            grave = await grave_from_result(result, db, name, url)
            j = await db.get(DigJob, job_id)
            if j:
                j.status = "done"
                j.message = "✅ Grave is ready."
                j.grave_slug = grave.slug
                await db.commit()

        # Set Sentry conversation ID to slug after grave is created
        if SENTRY_DSN:
            try:
                import sentry_sdk.ai
                sentry_sdk.ai.set_conversation_id(grave.slug)
            except Exception:
                pass

    except Exception as exc:
        logger.error(f"Dig job {job_id} failed: {exc}", exc_info=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(exc)
        async with AsyncSessionLocal() as db:
            j = await db.get(DigJob, job_id)
            if j:
                j.status = "failed"
                j.message = "❌ Dig failed."
                j.error = str(exc)[:900]
                await db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def cemetery(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Grave).where(Grave.dig_status == "done").order_by(desc(Grave.created_at))
    )
    graves = result.scalars().all()
    return templates.TemplateResponse("cemetery.html", {"request": request, "graves": graves})


@app.post("/bury")
@limiter.limit("3/hour")
async def bury(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    name: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    url = url.strip()
    name = name.strip()
    if not is_ssrf_safe(url):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL or target. IPs, localhost, non-HTTP schemes, and inputs > 200 chars are rejected."
        )

    # Normalize domain and check dedupe
    norm = normalize_domain(url)
    res_graves = await db.execute(select(Grave))
    for g in res_graves.scalars():
        if normalize_domain(g.url) == norm or (g.slug and g.slug == slugify(name or norm)):
            return JSONResponse({
                "job_id": None,
                "existing_slug": g.slug,
                "message": "Already in the graveyard.",
            })

    job_id = str(uuid.uuid4())
    job = DigJob(id=job_id, url=url, status="pending", message="Queued...")
    db.add(job)
    await db.commit()

    use_browserbase = bool(os.getenv("BROWSERBASE_API_KEY"))
    background_tasks.add_task(run_dig_job, job_id, url, name, use_browserbase)
    return JSONResponse({"job_id": job_id})


@app.get("/job/{job_id}")
async def job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(DigJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "status": job.status,
        "message": job.message,
        "grave_slug": job.grave_slug,
        "error": job.error,
    }


@app.get("/grave/{slug}", response_class=HTMLResponse)
async def grave_page(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grave).where(Grave.slug == slug))
    grave = result.scalar_one_or_none()
    if not grave:
        raise HTTPException(status_code=404, detail="Grave not found")

    lifeline = {}
    if grave.lifeline_json:
        try:
            lifeline = json.loads(grave.lifeline_json)
        except Exception:
            pass

    evidence = []
    if grave.cause_evidence:
        try:
            evidence = json.loads(grave.cause_evidence)
        except Exception:
            evidence = [grave.cause_evidence]

    claims = []
    if grave.claims_json:
        try:
            claims = json.loads(grave.claims_json)
        except Exception:
            pass

    attempts = []
    if grave.exhume_attempts:
        try:
            attempts = json.loads(grave.exhume_attempts)
        except Exception:
            pass

    memories = []
    if grave.memories_json:
        try:
            memories = json.loads(grave.memories_json)
        except Exception:
            pass

    return templates.TemplateResponse("grave.html", {
        "request": request,
        "grave": grave,
        "lifeline": lifeline,
        "evidence": evidence,
        "claims": claims,
        "attempts": attempts,
        "memories": memories,
    })


@app.post("/marigold/{slug}")
async def leave_marigold(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grave).where(Grave.slug == slug))
    grave = result.scalar_one_or_none()
    if not grave:
        raise HTTPException(status_code=404, detail="Grave not found")
    grave.marigolds = (grave.marigolds or 0) + 1
    await db.commit()
    return {"marigolds": grave.marigolds}


@app.post("/memory/{slug}")
@limiter.limit("5/hour")
async def leave_memory(
    request: Request,
    slug: str,
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    text = text.strip()[:500]
    if not text:
        raise HTTPException(status_code=400, detail="Memory cannot be empty")
    # Strip URLs to prevent link spam
    text = re.sub(r'https?://\S+', '', text).strip()
    if not text:
        raise HTTPException(status_code=400, detail="Memory cannot be empty")
    text = html_lib.escape(text)

    result = await db.execute(select(Grave).where(Grave.slug == slug))
    grave = result.scalar_one_or_none()
    if not grave:
        raise HTTPException(status_code=404, detail="Grave not found")

    memories = []
    if grave.memories_json:
        try:
            memories = json.loads(grave.memories_json)
        except Exception:
            pass
    memories.append({"text": text, "ts": datetime.utcnow().strftime("%b %d, %Y")})
    memories = memories[-50:]
    grave.memories_json = json.dumps(memories)
    await db.commit()
    return {"memories": memories}


@app.get("/benchmark", response_class=HTMLResponse)
async def benchmark_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BenchmarkResult).order_by(desc(BenchmarkResult.run_at))
    )
    rows = result.scalars().all()

    http_rows = [r for r in rows if r.path == "http"]
    bb_rows   = [r for r in rows if r.path == "browserbase"]

    def stats(rr):
        if not rr:
            return {
                "usable_pct": 0, "avg_secs": 0, "avg_chars": 0, "n": 0,
                "p50_ms": 0, "p95_ms": 0, "avg_fields": 0, "top_errors": [],
            }
        usable_cnt = sum(1 for r in rr if r.usable)
        usable_pct = 100 * usable_cnt / len(rr)
        secs_list = sorted([r.secs or 0.0 for r in rr])
        n = len(rr)
        p50 = secs_list[int(n * 0.5)] if secs_list else 0.0
        p95 = secs_list[int(n * 0.95)] if secs_list else 0.0
        avg_secs = sum(secs_list) / n
        avg_chars = sum(r.chars or 0 for r in rr) / n
        
        # Error frequencies
        errs = [r.error for r in rr if r.error]
        from collections import Counter
        top_errs = Counter(errs).most_common(3)

        return {
            "usable_pct": round(usable_pct, 1),
            "avg_secs": round(avg_secs, 1),
            "avg_chars": int(avg_chars),
            "p50_ms": int(p50 * 1000),
            "p95_ms": int(p95 * 1000),
            "avg_fields": round(sum(getattr(r, 'fields_filled', 0) or 0 for r in rr) / n, 1),
            "n": n,
            "top_errors": top_errs,
        }

    http_s = stats(http_rows)
    bb_s = stats(bb_rows)
    summary = {}
    if http_rows or bb_rows:
        summary["http"] = http_s
        summary["browserbase"] = bb_s

    # Breakdown by era (pre-2005 / 2005-2012 / post-2012)
    eras = {"pre-2005": [], "2005-2012": [], "post-2012": []}
    for r in rows:
        era = getattr(r, "era", None) or "2005-2012"
        if era in eras:
            eras[era].append(r)

    era_breakdown = {}
    for era_name, e_rows in eras.items():
        if e_rows:
            e_http = [r for r in e_rows if r.path == "http"]
            e_bb = [r for r in e_rows if r.path == "browserbase"]
            era_breakdown[era_name] = {
                "http_pct": round(100 * sum(1 for r in e_http if r.usable) / max(len(e_http), 1), 1),
                "bb_pct": round(100 * sum(1 for r in e_bb if r.usable) / max(len(e_bb), 1), 1),
                "total": len(e_rows),
            }

    return templates.TemplateResponse("benchmark.html", {
        "request": request,
        "rows": rows,
        "summary": summary,
        "http_stats": http_s,
        "bb_stats": bb_s,
        "era_breakdown": era_breakdown,
    })


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        from sqlalchemy import func
        res = await db.execute(select(func.count(Grave.id)))
        _ = res.scalar()
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "llm_provider": LLM_PROVIDER,
        "browserbase_configured": bool(os.getenv("BROWSERBASE_API_KEY")),
        "sentry_configured": bool(os.getenv("SENTRY_DSN")),
        "ts": datetime.utcnow().isoformat(),
    }
