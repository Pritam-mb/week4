import httpx
import json

url = "https://web.archive.org/cdx/search/cdx"
params = {
    "url": "www.google.com/reader",
    "output": "json",
    "fl": "timestamp,original,statuscode,mimetype",
    "collapse": "timestamp:6",
    "filter": "!statuscode:[45]..",
}
r = httpx.get(url, params=params, timeout=15)
data = r.json()
print("Total rows:", len(data) - 1)
status_counts = {}
for row in data[1:]:
    sc = row[2]
    status_counts[sc] = status_counts.get(sc, 0) + 1
print("Status code counts:", status_counts)

# Print a few 200s if any
twos = [row for row in data[1:] if row[2] == "200"]
print(f"200 count: {len(twos)}")
if twos:
    for t in twos[:5]:
        print("  200 snapshot:", t)

