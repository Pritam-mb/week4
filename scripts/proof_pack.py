#!/usr/bin/env python3
"""
scripts/proof_pack.py

Gathers and prints exact, unsummarized factual proof directly from
graveyard.db, benchmark.csv, spot_check.csv, and the codebase.

Outputs:
(1) Benchmark table per method (attempts, usable %, avg chars, p50, p95, failures by cause)
    plus per-site text lengths for Grooveshark and Pebble
(2) Fact-checker totals and percentages across all cemetery graves
(3) spot_check.csv agreement count
(4) Per-grave table: slug, chars recovered, cause, model, and the HTTP status of every exhume attempt
(5) Whether a LICENSE file exists
(6) Whether any exhume span stores a content hash
(7) Distinct values of llm_model
"""

import os
import sys
import csv
import json
import sqlite3
from pathlib import Path
import math

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "graveyard.db"
BENCHMARK_CSV = ROOT_DIR / "benchmark.csv"
SPOT_CHECK_CSV = ROOT_DIR / "spot_check.csv"
LICENSE_PATH = ROOT_DIR / "LICENSE"
PIPELINE_PATH = ROOT_DIR / "pipeline.py"


def percentile(data, pct):
    if not data:
        return 0.0
    k = (len(data) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    d0 = data[int(f)] * (c - k)
    d1 = data[int(c)] * (k - f)
    return d0 + d1


def section_1_benchmark():
    print("=" * 80)
    print("(1) BENCHMARK TABLE PER METHOD & PER-SITE TEXT LENGTHS")
    print("=" * 80)
    if not BENCHMARK_CSV.exists():
        print(f"ERROR: {BENCHMARK_CSV} not found.")
        return

    rows = []
    with open(BENCHMARK_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    by_method = {}
    for r in rows:
        path = r["path"].strip()
        by_method.setdefault(path, []).append(r)

    print(f"Total benchmark records: {len(rows)}")
    print()
    print(f"{'Method':<16} {'Attempts':<10} {'Usable':<8} {'Usable %':<10} {'Avg Chars':<12} {'p50 (s)':<10} {'p95 (s)':<10} {'Failures by Cause'}")
    print("-" * 105)

    for method, items in by_method.items():
        attempts = len(items)
        usable_items = [i for i in items if i["usable"].strip().lower() == "true"]
        usable_count = len(usable_items)
        usable_pct = (usable_count / attempts) * 100.0 if attempts else 0.0
        
        chars_list = [int(float(i["chars"])) for i in items]
        avg_chars = sum(chars_list) / len(chars_list) if chars_list else 0.0
        
        secs_list = sorted([float(i["secs"]) for i in items if i["secs"]])
        p50 = percentile(secs_list, 50)
        p95 = percentile(secs_list, 95)

        failures = {}
        for i in items:
            if i["usable"].strip().lower() != "true":
                err = i.get("error", "").strip()
                if not err:
                    err = "unusable (empty/block)"
                elif "402" in err or "Payment Required" in err:
                    err = "HTTP 402 / browser minutes limit"
                elif "timeout" in err.lower():
                    err = "timeout"
                failures[err] = failures.get(err, 0) + 1

        fail_str = "; ".join(f"{k}: {v}" for k, v in failures.items()) if failures else "0 failures"
        print(f"{method:<16} {attempts:<10} {usable_count:<8} {usable_pct:>7.1f}%  {avg_chars:>9.1f}   {p50:>8.1f}s  {p95:>8.1f}s  {fail_str}")

    print()
    print("Per-site text lengths for Grooveshark and Pebble:")
    for target in ["grooveshark", "pebble"]:
        matching = [r for r in rows if target in r["url"].lower()]
        print(f"  Target: {target} ({len(matching)} records)")
        for m in matching:
            print(f"    - method={m['path']:<12} usable={m['usable']:<6} chars={m['chars']:<6} secs={m['secs']:<5} url={m['url'][:65]}...")


def section_2_fact_checker():
    print()
    print("=" * 80)
    print("(2) FACT-CHECKER TOTALS AND PERCENTAGES")
    print("=" * 80)
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT slug, claims_json, unsupported_before, unsupported_after FROM graves ORDER BY slug")
    rows = c.fetchall()
    conn.close()

    total_claims = 0
    total_unsupported_before = 0
    total_unsupported_after = 0
    graves_with_claims = 0

    for slug, claims_json, unsupp_b, unsupp_a in rows:
        claims = []
        if claims_json:
            try:
                claims = json.loads(claims_json)
            except Exception:
                pass
        
        n_claims = len(claims)
        if n_claims > 0:
            graves_with_claims += 1
            total_claims += n_claims
        if unsupp_b is not None:
            total_unsupported_before += unsupp_b
        if unsupp_a is not None:
            total_unsupported_after += unsupp_a

    pct_before = (total_unsupported_before / total_claims * 100.0) if total_claims else 0.0
    pct_after = (total_unsupported_after / total_claims * 100.0) if total_claims else 0.0
    reduction = ((total_unsupported_before - total_unsupported_after) / total_unsupported_before * 100.0) if total_unsupported_before else 0.0

    print(f"Graves in database: {len(rows)}")
    print(f"Graves with generated claims: {graves_with_claims}")
    print(f"Total factual claims extracted: {total_claims}")
    print(f"Unsupported claims before rewrite: {total_unsupported_before} ({pct_before:.1f}%)")
    print(f"Unsupported claims after rewrite:  {total_unsupported_after} ({pct_after:.1f}%)")
    print(f"Net hallucination reduction:      {reduction:.1f}%")


def section_3_spot_check():
    print()
    print("=" * 80)
    print("(3) SPOT_CHECK.CSV AGREEMENT COUNT")
    print("=" * 80)
    if not SPOT_CHECK_CSV.exists():
        print(f"ERROR: {SPOT_CHECK_CSV} not found.")
        return

    with open(SPOT_CHECK_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    passes = sum(1 for r in rows if r.get("human_verified", "").strip().upper() == "PASS")
    revises = sum(1 for r in rows if r.get("human_verified", "").strip().upper() == "REVISE")
    other = total - passes - revises

    agreement_pct = (passes / total * 100.0) if total else 0.0

    print(f"Total spot-checked assertions: {total}")
    print(f"Human verified agreement (PASS): {passes} ({agreement_pct:.1f}%)")
    print(f"Human flagged revise/unsupported (REVISE): {revises}")
    if other:
        print(f"Other / unclassified: {other}")


def section_4_per_grave():
    print()
    print("=" * 80)
    print("(4) PER-GRAVE TABLE: SLUG, CHARS RECOVERED, CAUSE, MODEL, HTTP ATTEMPTS")
    print("=" * 80)
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT slug, name, extracted_text, cause_label, llm_model, exhume_attempts 
        FROM graves 
        ORDER BY slug
    """)
    rows = c.fetchall()
    conn.close()

    print(f"{'Slug':<22} {'Chars':<8} {'Cause':<26} {'Model':<22} {'Exhume HTTP Statuses'}")
    print("-" * 115)

    for slug, name, ext_text, cause, model, attempts_json in rows:
        chars = len(ext_text) if ext_text else 0
        cause_str = cause or "unknown"
        model_str = model or "None"

        statuses = []
        if attempts_json:
            try:
                attempts = json.loads(attempts_json)
                for att in attempts:
                    method = att.get("method", "http")
                    status = att.get("status", att.get("http_status", "?"))
                    chars_i = att.get("chars", 0)
                    statuses.append(f"{method}:{status}({chars_i}c)")
            except Exception:
                statuses = ["json_err"]

        status_str = ", ".join(statuses) if statuses else "no_attempts_logged"
        print(f"{slug:<22} {chars:<8} {cause_str:<26} {model_str:<22} {status_str}")


def section_5_license():
    print()
    print("=" * 80)
    print("(5) LICENSE FILE CHECK")
    print("=" * 80)
    if LICENSE_PATH.exists():
        size = LICENSE_PATH.stat().st_size
        with open(LICENSE_PATH, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        print(f"EXISTS: True ({LICENSE_PATH})")
        print(f"File size: {size} bytes")
        print(f"Header: {first_line}")
    else:
        print(f"EXISTS: False (No LICENSE file found at {LICENSE_PATH})")


def section_6_content_hash():
    print()
    print("=" * 80)
    print("(6) EXHUME SPAN CONTENT HASH CHECK")
    print("=" * 80)
    if not PIPELINE_PATH.exists():
        print(f"ERROR: {PIPELINE_PATH} not found.")
        return

    with open(PIPELINE_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    has_hash_in_pipeline = "hashlib.sha256" in code
    has_hash_in_attempt = '"body_hash":' in code or "'body_hash':" in code
    has_hash_in_span = False
    
    # Check if sentry span.set_data logs body_hash
    for line in code.splitlines():
        if "span.set_data" in line and ("hash" in line.lower() or "fingerprint" in line.lower()):
            has_hash_in_span = True
            break

    print(f"pipeline.py computes SHA256 body hash: {has_hash_in_pipeline}")
    print(f"pipeline.py records body_hash in attempt dict: {has_hash_in_attempt}")
    print(f"pipeline.py explicitly logs hash on sentry span data: {has_hash_in_span}")


def section_7_distinct_models():
    print()
    print("=" * 80)
    print("(7) DISTINCT VALUES OF llm_model IN graves")
    print("=" * 80)
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT llm_model FROM graves;")
    distinct = [r[0] for r in c.fetchall()]
    c.execute("SELECT COUNT(*), llm_model FROM graves GROUP BY llm_model;")
    breakdown = c.fetchall()
    conn.close()

    print(f"Distinct llm_model values: {distinct}")
    print(f"Breakdown: {breakdown}")


if __name__ == "__main__":
    section_1_benchmark()
    section_2_fact_checker()
    section_3_spot_check()
    section_4_per_grave()
    section_5_license()
    section_6_content_hash()
    section_7_distinct_models()
