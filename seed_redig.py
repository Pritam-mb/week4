"""
seed_redig.py — Re-dig all seed graves through the live pipeline.
Bypasses rate limits by calling the pipeline directly.
"""
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
    grave.dig_status = "done"

async def main():
    await init_db()
    if not SEED_PATH.exists():
        print("seed.json not found")
        return
    seeds = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    async with AsyncSessionLocal() as db:
        for item in seeds:
            slug = item["slug"]
            name = item["name"]
            url = item.get("url", "")
            if not url:
                logger.warning(f"Skip {slug} no url")
                continue
            # find existing grave
            res = await db.execute(select(Grave).where(Grave.slug == slug))
            grave = res.scalar_one_or_none()
            if not grave:
                logger.info(f"No existing grave for {slug}, skipping")
                continue
            logger.info(f"Re-digging {name} ({url})")
            # call pipeline
            async def status_callback(msg):
                logger.info(f"[{slug}] {msg}")
            try:
                result = await full_dig(url, name, use_browserbase=True, status_callback=status_callback)
                await update_grave_from_result(grave, result)
                await db.commit()
                logger.info(f"Done {slug}")
                # pacing
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Failed {slug}: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
