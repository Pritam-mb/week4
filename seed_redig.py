"""
seed_redig.py — Re-dig all seed graves through the live pipeline.
Bypasses rate limits by calling the pipeline directly.

Usage:
  python seed_redig.py          # Skip graves already done (dig_status=done)
  python seed_redig.py --force  # Re-dig all seeds regardless of status
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import asyncio
import json
import logging
from pathlib import Path
from database import init_db, Grave, AsyncSessionLocal
from sqlalchemy import select, delete
from pipeline import full_dig, GEMINI_MODEL, LLM_PROVIDER

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SEED_PATH = Path("seed.json")


async def update_grave_from_result(grave: Grave, result: dict, seed_item: dict):
    grave.first_archived = result.get("first_archived") or seed_item.get("first_archived")
    grave.last_seen_alive = result.get("last_seen_alive") or seed_item.get("last_seen_alive")
    grave.archive_url = result.get("archive_url") or seed_item.get("archive_url")
    grave.first_archive_url = result.get("first_archive_url") or seed_item.get("first_archive_url")
    grave.lifeline_json = result.get("lifeline_json")
    existing_shot = f"/static/screenshots/{grave.slug}.png" if Path(f"static/screenshots/{grave.slug}.png").exists() else None
    grave.screenshot_path = result.get("screenshot") or result.get("screenshot_path") or existing_shot or grave.screenshot_path
    grave.replay_url = result.get("replay") or grave.replay_url
    grave.extracted_text = result.get("extracted_text")
    grave.exhume_attempts = result.get("exhume_attempts")
    grave.extracted_fields_json = json.dumps(result.get("extracted_fields")) if result.get("extracted_fields") else None
    grave.epitaph = result.get("epitaph") or seed_item.get("epitaph") or grave.epitaph
    grave.eulogy = result.get("eulogy_verified") or result.get("eulogy") or seed_item.get("eulogy")
    
    # Coroner cause: use pipeline verdict if not unknown, otherwise use verified ground-truth from seed.json
    coroner_cause = result.get("cause_of_death")
    if coroner_cause and coroner_cause != "unknown":
        grave.cause_of_death = coroner_cause
        grave.cause_label = result.get("cause_label") or seed_item.get("cause_label")
    else:
        grave.cause_of_death = seed_item.get("cause_of_death") or "shut_down_by_owner"
        grave.cause_label = seed_item.get("cause_label") or "Shut down by owner"
        
    grave.cause_evidence = result.get("cause_evidence")
    grave.cause_is_rumored = result.get("cause_is_rumored", False)
    grave.survived_by = result.get("survived_by") or seed_item.get("survived_by")
    grave.eulogy_verified = result.get("eulogy_verified") or grave.eulogy
    grave.claims_json = result.get("claims_json")
    grave.unsupported_before = result.get("unsupported_before", 0)
    grave.unsupported_after = result.get("unsupported_after", 0)
    grave.llm_provider = result.get("llm_provider") or LLM_PROVIDER
    grave.llm_model = result.get("llm_model") or GEMINI_MODEL
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
        # Clean up legacy obsolete slugs from prior test runs if any
        obsolete_slugs = ["soundcloud-go", "tumblr-nsfw", "digg", "myspace"]
        for obs in obsolete_slugs:
            obs_res = await db.execute(select(Grave).where(Grave.slug == obs))
            obs_grave = obs_res.scalar_one_or_none()
            if obs_grave:
                logger.info(f"Removing obsolete test grave: {obs}")
                await db.delete(obs_grave)
                await db.commit()

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
            has_real_data = (
                grave.dig_status == "done"
                and grave.claims_json is not None
                and grave.exhume_attempts is not None
                and grave.llm_model == GEMINI_MODEL
            )
            if not args.force and has_real_data:
                logger.info(f"Skip {slug} already done with real data")
                results.append([slug, name, "SKIP", "already done", "-", "-", "-"])
                continue

            logger.info(f"Re-digging {name} ({url}) [launch={item.get('launch_year')}, death={item.get('death_year')}]")

            async def status_callback(msg):
                logger.info(f"[{slug}] {msg}")

            try:
                result = await full_dig(
                    url=url,
                    name=name,
                    use_browserbase=True,
                    status_callback=status_callback,
                    launch_year=item.get("launch_year"),
                    death_year=item.get("death_year"),
                    slug=slug,
                )
                await update_grave_from_result(grave, result, item)
                await db.commit()

                screenshot = "yes" if result.get("screenshot") else "no"
                replay = "yes" if result.get("replay") else "no"
                claims = f"{result.get('unsupported_before', 0)}->{result.get('unsupported_after', 0)}"
                results.append([slug, name, "DONE", "ok", screenshot, replay, claims])
                logger.info(f"Done {slug} ({result.get('first_archived')} - {result.get('last_seen_alive')})")

                # Pacing between digs
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Failed {slug}: {e}", exc_info=True)
                grave.dig_status = "failed"
                await db.commit()
                results.append([slug, name, "FAIL", str(e)[:60], "-", "-", "-"])
                await asyncio.sleep(2)

    # Print summary table
    print()
    print(f"{'Slug':<20} {'Name':<25} {'Status':<8} {'Detail':<20} {'Screenshot':<12} {'Replay':<8} {'Unsupported'}")
    print("-" * 105)
    for r in results:
        print(f"{r[0]:<20} {r[1]:<25} {r[2]:<8} {r[3]:<20} {r[4]:<12} {r[5]:<8} {r[6]}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
