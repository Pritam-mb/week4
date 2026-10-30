"""
scripts/metrics.py — Print markdown tables for the DEV post.
Metrics: exhume comparison, unsupported claims before→after, cause distribution,
avg tokens and seconds per dig.

Usage:
  python scripts/metrics.py
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import asyncio
import json
from collections import Counter
from database import init_db, Grave, BenchmarkResult, AsyncSessionLocal
from sqlalchemy import select, desc, func


async def main():
    await init_db()

    print("# Graveyard Metrics\n")

    # ── Exhume comparison (benchmark results) ──
    print("## Exhume Comparison (HTTP vs Browserbase)\n")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(BenchmarkResult).order_by(desc(BenchmarkResult.run_at)))
        rows = result.scalars().all()

    if not rows:
        print("_No benchmark rows yet. Run benchmark.py to populate._\n")
    else:
        http_rows = [r for r in rows if r.path == "http"]
        bb_rows = [r for r in rows if r.path == "browserbase"]

        def stats(rr):
            if not rr:
                return {"n": 0, "usable_pct": 0, "avg_chars": 0, "avg_fields": 0, "avg_secs": 0, "p50_ms": 0, "p95_ms": 0}
            usable = sum(1 for r in rr if r.usable)
            secs = sorted([r.secs or 0 for r in rr])
            n = len(rr)
            p50 = secs[int(n * 0.5)] if secs else 0
            p95 = secs[int(n * 0.95)] if secs else 0
            avg_fields = round(sum(getattr(r, "fields_filled", 0) or 0 for r in rr) / n, 1)
            return {
                "n": n,
                "usable_pct": round(100 * usable / n, 1),
                "avg_chars": int(sum(r.chars or 0 for r in rr) / n),
                "avg_fields": avg_fields,
                "avg_secs": round(sum(r.secs or 0 for r in rr) / n, 2),
                "p50_ms": int(p50 * 1000),
                "p95_ms": int(p95 * 1000),
            }

        http_s = stats(http_rows)
        bb_s = stats(bb_rows)

        print("| Method | N | Usable % | Avg Chars | Avg Fields | Avg Secs | p50 ms | p95 ms |")
        print("|--------|---|----------|-----------|------------|----------|--------|--------|")
        print(f"| HTTP | {http_s['n']} | {http_s['usable_pct']} | {http_s['avg_chars']} | {http_s['avg_fields']} | {http_s['avg_secs']} | {http_s['p50_ms']} | {http_s['p95_ms']} |")
        print(f"| Browserbase | {bb_s['n']} | {bb_s['usable_pct']} | {bb_s['avg_chars']} | {bb_s['avg_fields']} | {bb_s['avg_secs']} | {bb_s['p50_ms']} | {bb_s['p95_ms']} |")
        print()

    # ── Unsupported claims before→after ──
    print("## Fact-Checker: Unsupported Claims Before → After\n")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Grave).where(Grave.claims_json.is_not(None))
        )
        graves = result.scalars().all()

    if not graves:
        print("_No fact-checked graves yet._\n")
    else:
        total_before = 0
        total_after = 0
        total_claims = 0
        for g in graves:
            try:
                claims = json.loads(g.claims_json or "[]")
                total_claims += len(claims)
                total_before += g.unsupported_before or 0
                total_after += g.unsupported_after or 0
            except Exception:
                pass

        print(f"| Metric | Value |")
        print(f"|--------|-------|")
        print(f"| Total graves fact-checked | {len(graves)} |")
        print(f"| Total claims | {total_claims} |")
        print(f"| Unsupported before | {total_before} |")
        print(f"| Unsupported after | {total_after} |")
        print(f"| Reduction | {total_before - total_after} |")
        print()

    # ── Cause distribution ──
    print("## Cause of Death Distribution\n")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Grave.cause_label, func.count(Grave.id))
            .where(Grave.cause_label.is_not(None))
            .group_by(Grave.cause_label)
            .order_by(func.count(Grave.id).desc())
        )
        cause_rows = result.all()

    if not cause_rows:
        print("_No cause data yet._\n")
    else:
        print("| Cause | Count |")
        print("|-------|-------|")
        for label, count in cause_rows:
            print(f"| {label} | {count} |")
        print()

    # ── Avg tokens and seconds per dig ──
    print("## Dig Performance\n")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Grave).where(Grave.dig_status == "done"))
        done_graves = result.scalars().all()

    if not done_graves:
        print("_No completed digs yet._\n")
    else:
        total_attempts = 0
        total_ms = 0
        for g in done_graves:
            try:
                attempts = json.loads(g.exhume_attempts or "[]")
                total_attempts += len(attempts)
                for a in attempts:
                    total_ms += a.get("ms", 0)
            except Exception:
                pass

        avg_ms = total_ms / max(total_attempts, 1)
        print(f"| Metric | Value |")
        print(f"|--------|-------|")
        print(f"| Completed digs | {len(done_graves)} |")
        print(f"| Total exhume attempts | {total_attempts} |")
        print(f"| Avg ms per attempt | {avg_ms:.0f} |")
        print()


if __name__ == "__main__":
    asyncio.run(main())
