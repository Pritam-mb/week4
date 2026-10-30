import os
from dotenv import load_dotenv
load_dotenv()

from browserbase import Browserbase
from playwright.sync_api import sync_playwright

api_key = os.getenv("BROWSERBASE_API_KEY")
bb = Browserbase(api_key=api_key)
session = bb.sessions.create()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(session.connect_url)
    page = browser.contexts[0].pages[0]
    
    url = "https://web.archive.org/web/20161028000000/https://vine.co/"
    page.goto(url, wait_until="load", timeout=30000)
    
    content = page.content()
    print("Content length:", len(content))
    print("Content snippet:\n", content[:1000])
    print("Frames count:", len(page.frames))
    for f in page.frames:
        print("Frame:", f.name, f.url)
        try:
            ft = f.inner_text("body")
            print("  Frame inner_text len:", len(ft))
            if len(ft) > 0:
                print("  Sample:", ft[:200])
        except Exception as e:
            print("  Frame inner_text error:", e)
    
    browser.close()
