import sqlite3
import json

conn = sqlite3.connect("graveyard.db")
c = conn.cursor()
c.execute("PRAGMA table_info(graves)")
cols = [r[1] for r in c.fetchall()]
print("Columns:", cols)

c.execute("SELECT * FROM graves WHERE slug='google-reader'")
row = c.fetchone()
if row:
    data = dict(zip(cols, row))
    attempts = json.loads(data.get("exhume_attempts") or "[]")
    print(f"\nAttempts count: {len(attempts)}")
    for a in attempts:
        print(f"[{a.get('evidence_id')}] method={a.get('method')} status={a.get('status')} chars={a.get('chars')} error={a.get('error')}")
        print(f"  Link: {a.get('link')}")
        print(f"  Text preview: {repr(a.get('text', '')[:200])}")
    print("\nEpitaph:", data.get("epitaph"))
    print("Eulogy:", data.get("eulogy"))
    print("Cause of death:", data.get("cause_of_death"))
    print("Cause label:", data.get("cause_label"))
    print("Evidence used:", data.get("cause_evidence"))
    print("Claims:", data.get("factcheck_claims"))
    print(f"Unsupported: before={data.get('unsupported_before')}, after={data.get('unsupported_after')}")
    print("Screenshot:", data.get("screenshot_path"))
    print("Replay:", data.get("replay_url"))
    print("Provider/Model:", data.get("llm_provider"), "/", data.get("llm_model"))
