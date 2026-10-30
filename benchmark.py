"""
benchmark.py — Eval A: HTTP vs Browserbase on 35 archived dead sites
Run: venv\Scripts\python.exe benchmark.py
Writes benchmark.csv and inserts rows into benchmark_results table.
"""

import asyncio
import csv
import json
import time
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

BENCHMARK_FILE = Path("benchmark.json")
OUT_CSV        = Path("benchmark.csv")


async def run_benchmark():
    from dotenv import load_dotenv
    load_dotenv()

    from pipeline import (
        wayback_snapshots, exhume_with_browserbase, exhume_without_browser,
        build_archive_url, usable,
    )
    from database import init_db, AsyncSessionLocal, BenchmarkResult

    await init_db()

    urls_meta: list[dict] = json.loads(BENCHMARK_FILE.read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(urls_meta)} URLs from benchmark.json")

    rows = []

    for meta in urls_meta:
        url = meta["url"]
        site_type = meta.get("type", "unknown")

        snaps = await wayback_snapshots(url, n=1)
        if not snaps:
            logger.warning(f"No snapshots for {url} — skipping")
            for path_name in ["http", "browserbase"]:
                rows.append({
                    "url": url, "site_type": site_type, "path": path_name,
                    "usable": False, "chars": 0, "secs": 0,
                    "error": "no_snapshots",
                })
            continue

        archive_link = build_archive_url(snaps[0]["timestamp"], snaps[0]["original"])
        logger.info(f"Testing {url} -> {archive_link}")

        for path_name, fn in [("http", "async"), ("browserbase", "sync")]:
            t0 = time.time()
            try:
                if path_name == "http":
                    res = await exhume_without_browser(archive_link)
                else:
                    loop = asyncio.get_event_loop()
                    res = await loop.run_in_executor(None, exhume_with_browserbase, archive_link)

                text = res.get("text", "") or ""
                ok   = usable(text)
                chars = len(text)
                err  = res.get("error") or ""
            except Exception as e:
                ok, chars, err = False, 0, type(e).__name__

            elapsed = round(time.time() - t0, 1)
            row = {
                "url": url, "site_type": site_type, "path": path_name,
                "usable": ok, "chars": chars, "secs": elapsed, "error": err,
            }
            rows.append(row)
            logger.info(f"  [{path_name}] usable={ok} chars={chars} secs={elapsed} err={err}")

    # Write CSV
    if rows:
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["url","site_type","path","usable","chars","secs","error"])
            w.writeheader()
            w.writerows(rows)
        logger.info(f"Wrote {OUT_CSV}")

    # Save to DB
    async with AsyncSessionLocal() as db:
        for row in rows:
            db.add(BenchmarkResult(
                url=row["url"], site_type=row["site_type"], path=row["path"],
                usable=bool(row["usable"]), chars=int(row["chars"]),
                secs=float(row["secs"]), error=row["error"] or None,
            ))
        await db.commit()
    logger.info("Saved to DB")

    # Print summary
    print("\n=== SUMMARY ===")
    for path_name in ["http", "browserbase"]:
        path_rows = [r for r in rows if r["path"] == path_name]
        if not path_rows:
            continue
        usable_pct = 100 * sum(1 for r in path_rows if r["usable"]) / len(path_rows)
        avg_chars  = sum(r["chars"] for r in path_rows) / len(path_rows)
        avg_secs   = sum(r["secs"] for r in path_rows) / len(path_rows)
        print(f"{path_name:15s}: usable={usable_pct:.1f}%  avg_chars={avg_chars:.0f}  avg_secs={avg_secs:.1f}s")

    # By type
    print("\n=== BY TYPE ===")
    types = sorted(set(r["site_type"] for r in rows))
    for t in types:
        for path_name in ["http", "browserbase"]:
            trows = [r for r in rows if r["site_type"] == t and r["path"] == path_name]
            if trows:
                upct = 100 * sum(1 for r in trows if r["usable"]) / len(trows)
                print(f"  {t:12s} [{path_name:12s}]: usable={upct:.0f}%  n={len(trows)}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
