import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio, json
from pipeline import full_dig
from database import init_db, AsyncSessionLocal, Grave
from sqlalchemy import select
from seed_redig import update_grave_from_result

async def main():
    await init_db()
    name = "Google Reader"
    url = "https://www.google.com/reader"
    print(f"Starting live dig for {name} ({url})...")

    async def callback(msg):
        print(f"  [STAGE] {msg}")

    result = await full_dig(url, name, use_browserbase=True, status_callback=callback)

    print("\n=== DIG RESULTS ===")
    print("Name:", result.get("name"))
    print("First archived:", result.get("first_archived"))
    print("Last seen alive:", result.get("last_seen_alive"))
    print("Lifeline JSON length:", len(result.get("lifeline_json") or ""))
    print("Screenshot:", result.get("screenshot"))
    print("Replay URL:", result.get("replay"))
    print("Cause label:", result.get("cause_label"))
    print("Cause of death:", result.get("cause_of_death"))
    print("Cause evidence:", result.get("cause_evidence"))
    print("Epitaph:", result.get("epitaph"))
    print("Eulogy:", result.get("eulogy"))
    print("Eulogy verified:", result.get("eulogy_verified"))
    print("Unsupported before:", result.get("unsupported_before"))
    print("Unsupported after:", result.get("unsupported_after"))
    print("Claims count:", len(json.loads(result.get("claims_json") or "[]")))

    attempts = json.loads(result.get("exhume_attempts") or "[]")
    print(f"Exhume attempts count: {len(attempts)}")
    for a in attempts:
        print(f"  [{a['evidence_id']}] {a['ts']} method={a['method']} status={a['status']} chars={a['chars']} ms={a['ms']}")

    # Save to database
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Grave).where(Grave.slug == "google-reader"))
        grave = res.scalar_one_or_none()
        if grave:
            await update_grave_from_result(grave, result)
            await db.commit()
            print("\nSuccessfully updated google-reader grave in graveyard.db with real data!")

if __name__ == "__main__":
    asyncio.run(main())
