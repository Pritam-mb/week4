import httpx
import re

url = "https://www.geocities.com"
clean = re.sub(r"^https?://(?:www\.)?", "", url.strip()).rstrip("/")
print("Clean:", clean)

CDX_BASE = "https://web.archive.org/cdx/search/cdx"

# Fallback: get first 200 and last 100
r_old = httpx.get(CDX_BASE, params={"url": clean, "output": "json", "fl": "timestamp,original,statuscode", "limit": "200"}, timeout=15)
old_rows = r_old.json()[1:] if r_old.status_code == 200 else []
print("Old rows:", len(old_rows))

r_new = httpx.get(CDX_BASE, params={"url": clean, "output": "json", "fl": "timestamp,original,statuscode", "limit": "-100"}, timeout=15)
new_rows = r_new.json()[1:] if r_new.status_code == 200 else []
print("New rows:", len(new_rows))

all_rows = old_rows + new_rows
print("Combined rows:", len(all_rows))
print("First snapshot:", all_rows[0])
print("Last snapshot:", all_rows[-1])

# Build lifeline
by_year = {}
for r in all_rows:
    yr = r[0][:4]
    by_year[yr] = by_year.get(yr, 0) + 1
print("Lifeline years:", sorted(by_year.keys()))

