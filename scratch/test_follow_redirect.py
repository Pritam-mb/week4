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
    
    url = "https://web.archive.org/web/20100411010250/http://www.google.com/reader"
    print("Navigating to:", url)
    page.goto(url, wait_until="load", timeout=30000)
    
    # Check if Wayback redirect interstitial is showing
    impatient = page.query_selector("p.impatient a, a.impatient")
    print("Impatient link found?", impatient is not None)
    if impatient:
        target = impatient.get_attribute("href")
        print("Target href:", target)
        if target:
            if target.startswith("/"):
                target = "https://web.archive.org" + target
            print("Navigating to target:", target)
            page.goto(target, wait_until="load", timeout=30000)
    
    print("Final URL:", page.url)
    print("Page Title:", page.title())
    body_text = page.inner_text("body")
    print("Body text len:", len(body_text))
    print("Body snippet:\n", body_text[:400])
    
    browser.close()

