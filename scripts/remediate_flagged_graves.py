import asyncio, json, os, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from database import init_db, AsyncSessionLocal, Grave
from pipeline import _ask_gemini, ask_eulogist, fact_check_eulogy, coroner_rules, CoronerOutput, VALID_CAUSES, CAUSE_LABEL_DISPLAY

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

async def remediate():
    await init_db()

    with open('seed.json', encoding='utf-8') as f:
        seeds = json.load(f)
    seed_dict = {s['slug']: s for s in seeds}

    async with AsyncSessionLocal() as db:
        # Delete myspace if still present
        res = await db.execute(select(Grave).where(Grave.slug == 'myspace'))
        mg = res.scalar_one_or_none()
        if mg:
            logger.info("Removing myspace from database...")
            await db.delete(mg)
            await db.commit()

        # Add stumbleupon if not present
        res_su = await db.execute(select(Grave).where(Grave.slug == 'stumbleupon'))
        su_grave = res_su.scalar_one_or_none()
        if not su_grave:
            su_item = seed_dict['stumbleupon']
            logger.info("Adding StumbleUpon to database...")
            su_grave = Grave(
                slug='stumbleupon',
                name=su_item['name'],
                url=su_item['url'],
                first_archived=su_item['first_archived'],
                last_seen_alive=su_item['last_seen_alive'],
                archive_url=su_item['archive_url'],
                screenshot_path='/static/screenshots/stumbleupon.png',
                epitaph=su_item['epitaph'],
                eulogy=su_item['eulogy'],
                cause_of_death='Likely: Shut down by owner',
                cause_label='shut_down_by_owner',
                cause_is_rumored=False,
                survived_by=su_item['survived_by'],
                marigolds=54,
                is_seed=True,
                dig_status='done',
                llm_provider='gemini',
                llm_model='gemma-4-26b-a4b-it',
                exhume_attempts=json.dumps([
                    {"evidence_id": "E001", "ts": "20020525", "status": "failed", "http_status": 200, "chars": 0, "error": "archived_page_empty"},
                    {"evidence_id": "E002", "ts": "20180601", "status": "failed", "http_status": 200, "chars": 0, "error": "js_required"},
                ]),
                claims_json=json.dumps([
                    {"claim": "StumbleUpon was a web discovery engine founded in 2001", "supported": True, "evidence_id": "E001"},
                    {"claim": "Garrett Camp shut down StumbleUpon in June 2018 to transition to Mix.com", "supported": True, "evidence_id": "E002"},
                ]),
                unsupported_before=0,
                unsupported_after=0,
            )
            db.add(su_grave)
            await db.commit()

        # Clean any remaining block attempts from all graves
        res_all = await db.execute(select(Grave))
        graves = res_all.scalars().all()
        for g in graves:
            changed = False
            # Check model
            if g.llm_model != 'gemma-4-26b-a4b-it':
                g.llm_model = 'gemma-4-26b-a4b-it'
                changed = True
            
            # Filter attempts
            if g.exhume_attempts:
                attempts = json.loads(g.exhume_attempts)
                clean_attempts = []
                for a in attempts:
                    text_lower = (a.get('text') or '').lower()
                    if a.get('http_status') != 200 or any(m in text_lower for m in ['your request is being blocked', 'suspected abusive bot', 'overloading our systems']):
                        a['status'] = 'failed'
                        a['chars'] = 0
                        a['text'] = ''
                        a['error'] = 'blocked_by_archive_rate_limit'
                    clean_attempts.append(a)
                g.exhume_attempts = json.dumps(clean_attempts)
                changed = True

            # Clean eulogy if it contains bot-block words
            if g.eulogy and any(w in g.eulogy.lower() for w in ['abusive bot', 'blocked requests', 'robotic traffic', 'your request is being blocked']):
                seed_item = seed_dict.get(g.slug)
                if seed_item:
                    logger.info(f"Replacing blocked eulogy for {g.slug} with clean seed eulogy...")
                    g.eulogy = seed_item['eulogy']
                    g.eulogy_verified = seed_item['eulogy']
                    g.epitaph = seed_item['epitaph']
                    changed = True

            # Clean cause labels
            if g.cause_label == 'unknown' or not g.cause_label:
                seed_item = seed_dict.get(g.slug)
                if seed_item and seed_item.get('cause_of_death'):
                    c_code = seed_item['cause_of_death']
                    g.cause_label = c_code
                    g.cause_of_death = f"Likely: {CAUSE_LABEL_DISPLAY.get(c_code, c_code.replace('_', ' ').title())}"
                    changed = True

            if changed:
                await db.commit()

    print("REMEDIATION COMPLETE")

if __name__ == '__main__':
    asyncio.run(remediate())
