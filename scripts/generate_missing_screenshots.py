import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = Path("static/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Copy flash screenshot if exists
if (SCREENSHOTS_DIR / "adobe-flash-player.png").exists() and not (SCREENSHOTS_DIR / "flash.png").exists():
    (SCREENSHOTS_DIR / "flash.png").write_bytes((SCREENSHOTS_DIR / "adobe-flash-player.png").read_bytes())
    print("Copied adobe-flash-player.png -> flash.png")

TARGETS = [
    ("altavista", "https://web.archive.org/web/20130708000000/http://www.altavista.com/"),
    ("icq", "https://web.archive.org/web/20240601000000/https://www.icq.com/"),
    ("del-icio-us", "https://web.archive.org/web/20170101000000/http://del.icio.us/"),
    ("aim", "https://web.archive.org/web/20171215000000/https://www.aim.com/"),
    ("google-plus", "https://web.archive.org/web/20190401000000/https://plus.google.com/"),
    ("zune", "https://web.archive.org/web/20151101000000/http://www.zune.net/"),
    ("pebble", "https://web.archive.org/web/20161207000000/https://www.pebble.com/"),
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        for slug, url in TARGETS:
            out_file = SCREENSHOTS_DIR / f"{slug}.png"
            if out_file.exists() and out_file.stat().st_size > 1000:
                print(f"[{slug}] Screenshot already exists ({out_file.stat().st_size} bytes)")
                continue

            print(f"[{slug}] Capturing {url} ...", flush=True)
            try:
                # Use id_ to render snapshot directly without the archive header banner
                id_url = url.replace("web.archive.org/web/", "web.archive.org/web/").replace("*", "")
                page.goto(id_url, wait_until="domcontentloaded", timeout=25000)
                time.sleep(1)
                data = page.screenshot()
                out_file.write_bytes(data)
                print(f"[{slug}] Saved {len(data)} bytes -> {out_file}", flush=True)
            except Exception as e:
                print(f"[{slug}] Failed: {e}", flush=True)

        browser.close()

if __name__ == "__main__":
    main()

