"""
seed_db.py — Run this once to seed the database from seed.json without starting the server.
Usage: python seed_db.py
"""
import asyncio
import json
from pathlib import Path
from database import init_db, Grave, AsyncSessionLocal
from sqlalchemy import select


async def main():
    await init_db()
    seed_path = Path("seed.json")
    if not seed_path.exists():
        print("seed.json not found")
        return

    data = json.loads(seed_path.read_text(encoding="utf-8"))
    async with AsyncSessionLocal() as db:
        count = 0
        for item in data:
            existing = await db.execute(select(Grave).where(Grave.slug == item["slug"]))
            if existing.scalar_one_or_none():
                print(f"  SKIP  {item['slug']} (already exists)")
                continue
            grave = Grave(
                slug=item["slug"],
                name=item["name"],
                url=item.get("url", ""),
                first_archived=item.get("first_archived"),
                last_seen_alive=item.get("last_seen_alive"),
                archive_url=item.get("archive_url"),
                epitaph=item.get("epitaph"),
                eulogy=item.get("eulogy"),
                cause_of_death=item.get("cause_of_death"),
                cause_is_rumored=item.get("cause_is_rumored", True),
                survived_by=item.get("survived_by"),
                marigolds=item.get("marigolds", 0),
                is_seed=True,
                dig_status="done",
            )
            db.add(grave)
            count += 1
            print(f"  ADD   {item['slug']}")
        await db.commit()
    print(f"\nDone. Added {count} new graves.")


if __name__ == "__main__":
    asyncio.run(main())
