"""
seed_redig.py — Re-dig all seed graves through the live pipeline.
Bypasses rate limits by calling the pipeline directly.

Usage:
  python seed_redig.py          # Skip graves already done (dig_status=done)
  python seed_redig.py --force  # Re-dig all seeds regardless of status
"""
import argparse
import asyncio
import json
import logging
from pathlib import Path
from database import init_db, Grave, AsyncSessionLocal
from sqlalchemy import select
from pipeline import full_dig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SEED_PATH = Path("seed.json")


async def update_grave_from_result(grave: Grave, result: dict):
    grave.first_archived = result.get("first_archived")
    grave.last_seen_alive = result.get("last_seen_alive")
    grave.archive_url = result.get("archive_url")
    grave.first_archive_url = result.get("first_archive_url")
    grave.lifeline_json = result.get("lifeline_json")
    grave.screenshot_path = result.get("screenshot_path") or grave.screenshot_path
    grave.replay_url = result.get("replay")
    grave.extracted_text = result.get("extracted_text")
    grave.exhume_attempts = result.get("exhume_attempts")
    grave.extracted_fields_json = json.dumps(result.get("extracted_fields")) if result.get("extracted_fields") else None
    grave.epitaph = result.get("epitaph") or grave.epitaph
    grave.eulogy = result.get("eulogy")
    grave.cause_of_death = result.get("cause_of_death")
    grave.cause_label = result.get("cause_label")
    grave.cause_evidence = result.get("cause_evidence")
    grave.cause_is_rumored = result.get("cause_is_rumored", True)
    grave.survived_by = result.get("survived_by")
    grave.eulogy_verified = result.get("eulogy_verified")
    grave.claims_json = result.get("claims_json")
    grave.unsupported_before = result.get("unsupported_before")
    grave.unsupported_after = result.get("unsupported_after")
    grave.llm_provider = result.get("llm_provider")
    grave.llm_model = result.get("llm_model")
    grave.dig_status = "done"
    grave.is_seed = True


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-dig all seeds even if already done")
    args = parser.parse_args()

    await init_db()
    if not SEED_PATH.exists():
        print("seed.json not found")
        return
    seeds = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    results = []
    async with AsyncSessionLocal() as db:
        for item in seeds:
            slug = item["slug"]
            name = item["name"]
            url = item.get("url", "")
            if not url:
                logger.warning(f"Skip {slug} no url")
                results.append([slug, name, "SKIP", "no url", "-", "-", "-"])
                continue

            res = await db.execute(select(Grave).where(Grave.slug == slug))
            grave = res.scalar_one_or_none()
            if not grave:
                logger.info(f"No existing grave for {slug}, creating")
                grave = Grave(
                    slug=slug, name=name, url=url,
                    is_seed=True, dig_status="pending",
                )
                db.add(grave)
                await db.commit()
                await db.refresh(grave)

            # Check if grave was already dug with real pipeline data
            has_real_data = grave.dig_status == "done" and grave.claims_json is not None and grave.exhume_attempts is not None
            if not args.force and has_real_data:
                logger.info(f"Skip {slug} already done with real data")
                results.append([slug, name, "SKIP", "already done", "-", "-", "-"])
                continue

            logger.info(f"Re-digging {name} ({url})")

            async def status_callback(msg):
                logger.info(f"[{slug}] {msg}")

            try:
                result = await full_dig(url, name, use_browserbase=True, status_callback=status_callback)
                await update_grave_from_result(grave, result)
                await db.commit()

                screenshot = "yes" if result.get("screenshot") else "no"
                replay = "yes" if result.get("replay") else "no"
                claims = result.get("unsupported_before", 0)
                results.append([slug, name, "DONE", "ok", screenshot, replay, str(claims)])
                logger.info(f"Done {slug}")

                # pacing to respect free-tier limits
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Failed {slug}: {e}")
                grave.dig_status = "failed"
                await db.commit()
                results.append([slug, name, "FAIL", str(e)[:60], "-", "-", "-"])
                await asyncio.sleep(5)

    # Print summary table
    print()
    print(f"{'Slug':<20} {'Name':<25} {'Status':<8} {'Detail':<20} {'Screenshot':<12} {'Replay':<8} {'Unsupported'}")
    print("-" * 105)
    for r in results:
        print(f"{r[0]:<20} {r[1]:<25} {r[2]:<8} {r[3]:<20} {r[4]:<12} {r[5]:<8} {r[6]}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
