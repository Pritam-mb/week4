import httpx
r = httpx.get("https://web.archive.org/web/20100411010250/http://www.google.com/reader", follow_redirects=True)
print("Final URL:", r.url)
print("Status code:", r.status_code)
print("Headers:", dict(r.headers))
print("Body length:", len(r.text))
print("Body snippet:\n", r.text[:500])

