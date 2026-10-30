"""
seed_bundle.py — Export DB + screenshots for committing as a seed bundle.
Creates ./seed_bundle/seed_bundle.zip containing graveyard.db and static/screenshots/
"""
import asyncio
import shutil
from pathlib import Path
from zipfile import ZipFile
from database import init_db

BUNDLE_DIR = Path("seed_bundle")
DB_PATH = Path("graveyard.db")
SCREENSHOTS = Path("static/screenshots")
OUT_ZIP = BUNDLE_DIR / "seed_bundle.zip"

async def main():
    await init_db()
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    # copy db
    shutil.copy2(DB_PATH, BUNDLE_DIR / "graveyard.db")
    # copy screenshots
    dest_screens = BUNDLE_DIR / "screenshots"
    if SCREENSHOTS.exists():
        shutil.copytree(SCREENSHOTS, dest_screens, dirs_exist_ok=True)
    # zip
    with ZipFile(OUT_ZIP, "w") as z:
        for p in BUNDLE_DIR.rglob("*"):
            if p.is_file() and p != OUT_ZIP:
                z.write(p, arcname=str(p.relative_to(BUNDLE_DIR)))
    print(f"Bundle written to {OUT_ZIP}")

if __name__ == "__main__":
    asyncio.run(main())
