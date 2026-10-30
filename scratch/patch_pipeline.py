import re

with open("pipeline.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update BAD_MARKERS and usable
old_bad = '''BAD_MARKERS = [
    "this site has moved", "page not found", "redirecting", "access denied",
    "enable javascript", "domain for sale", "account suspended",
    "this domain is for sale", "parked by", "this page is no longer",
    "site unavailable", "error 404", "403 forbidden",
]

def usable(text: str) -> bool:
    t = text.lower().strip()
    return len(t) > 400 and not any(m in t[:800] for m in BAD_MARKERS)'''

new_bad = '''BAD_MARKERS = [
    "this site has moved", "page not found", "access denied",
    "enable javascript", "domain for sale", "account suspended",
    "this domain is for sale", "parked by", "this page is no longer",
    "site unavailable", "error 404", "403 forbidden",
    "got an http 302 response", "got an http 301 response",
    "redirecting to...",
]

def usable(text: str, fields_filled: int = 0) -> bool:
    t = text.lower().strip()
    if fields_filled > 0 and len(t) >= 50:
        return True
    return len(t) >= 100 and not any(m in t[:800] for m in BAD_MARKERS)'''

assert old_bad in content, "old_bad not found"
content = content.replace(old_bad, new_bad)

# 2. Update Browserbase goto, redirect follow, and frames
old_bb_goto = '''            try:
                page.goto(archive_link, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                try:
                    page.goto(archive_link, wait_until="commit", timeout=30000)
                except Exception as e2:
                    logger.warning(f"Browserbase goto failed: {e2}")
                    browser.close()
                    return {"title": "", "text": "", "screenshot": None, "replay": replay_url, "error": "timeout",
                            "fields_filled": 0, "evidence_id": None}

            title = page.title() or ""
            raw_text = ""
            try:
                raw_text = page.inner_text("body") or ""
            except Exception:
                pass

            text = _clean_wayback_text(raw_text)[:6000]'''

new_bb_goto = '''            try:
                page.goto(archive_link, wait_until="load", timeout=30000)
            except Exception:
                try:
                    page.goto(archive_link, wait_until="domcontentloaded", timeout=20000)
                except Exception as e2:
                    logger.warning(f"Browserbase goto failed: {e2}")
                    browser.close()
                    return {"title": "", "text": "", "screenshot": None, "replay": replay_url, "error": "timeout",
                            "fields_filled": 0, "evidence_id": None}

            # Follow Wayback redirect interstitial if present
            try:
                impatient = page.query_selector("p.impatient a, a.impatient, a:has-text('Impatient?')")
                if impatient:
                    target = impatient.get_attribute("href")
                    if target:
                        if target.startswith("/"):
                            target = "https://web.archive.org" + target
                        page.goto(target, wait_until="load", timeout=25000)
            except Exception as e_redir:
                logger.debug(f"Wayback redirect follow error: {e_redir}")

            title = page.title() or ""
            raw_text = ""
            try:
                raw_text = page.inner_text("body") or ""
            except Exception:
                pass

            if len(raw_text.strip()) < 50:
                for f in page.frames:
                    try:
                        ft = f.inner_text("body") or ""
                        if len(ft.strip()) > len(raw_text.strip()):
                            raw_text = ft
                    except Exception:
                        pass

            text = _clean_wayback_text(raw_text)[:6000]'''

assert old_bb_goto in content, "old_bb_goto not found"
content = content.replace(old_bb_goto, new_bb_goto)

# 3. Fix line 525 raw_link regex
content = re.sub(r'raw_link = re\.sub\(r"/web/\(\\d\+\)/", [^\n]+, archive_link\)', 'raw_link = re.sub(r"/web/(\\\\d+)/", r"/web/\\\\g<1>id_/", archive_link)', content)

# 4. In exhume_best: pass fields_filled to usable
old_ladder = '''                if res.get("error") or not usable(res.get("text", "")):
                    logger.info(f"[{evidence_id}] Browserbase fallback to HTTP for {link}")
                    fallback_res = await exhume_without_browser(link)
                    if usable(fallback_res.get("text", "")):
                        # Retain screenshot/replay from browserbase if captured
                        fallback_res["screenshot"] = res.get("screenshot") or fallback_res.get("screenshot")
                        fallback_res["replay"] = res.get("replay") or fallback_res.get("replay")
                        res = fallback_res
                        method = "http"'''

new_ladder = '''                if res.get("error") or not usable(res.get("text", ""), res.get("fields_filled", 0)):
                    logger.info(f"[{evidence_id}] Browserbase fallback to HTTP for {link}")
                    fallback_res = await exhume_without_browser(link)
                    if usable(fallback_res.get("text", ""), fallback_res.get("fields_filled", 0)):
                        # Retain screenshot/replay from browserbase if captured
                        fallback_res["screenshot"] = res.get("screenshot") or fallback_res.get("screenshot")
                        fallback_res["replay"] = res.get("replay") or fallback_res.get("replay")
                        res = fallback_res
                        method = "http"'''

assert old_ladder in content, "old_ladder not found"
content = content.replace(old_ladder, new_ladder)

old_ok = '''        elapsed = round(time.time() - t0, 1)
        text = res.get("text", "") or ""
        ok = usable(text)
        fields_filled = res.get("fields_filled", 0)'''

new_ok = '''        elapsed = round(time.time() - t0, 1)
        text = res.get("text", "") or ""
        fields_filled = res.get("fields_filled", 0)
        ok = usable(text, fields_filled)'''

assert old_ok in content, "old_ok not found"
content = content.replace(old_ok, new_ok)

# 5. In full_dig: screenshot_path key
old_res_sc = '''    result["screenshot"] = fetch_result.get("screenshot")
    result["replay"]     = fetch_result.get("replay")'''

new_res_sc = '''    result["screenshot"] = fetch_result.get("screenshot")
    result["screenshot_path"] = result["screenshot"]
    result["replay"]     = fetch_result.get("replay")'''

assert old_res_sc in content, "old_res_sc not found"
content = content.replace(old_res_sc, new_res_sc)

with open("pipeline.py", "w", encoding="utf-8") as f:
    f.write(content)

print("pipeline.py patched successfully!")
