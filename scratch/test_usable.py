import sys
sys.path.insert(0, ".")
import sqlite3
import json
from pipeline import usable, BAD_MARKERS

conn = sqlite3.connect("graveyard.db")
c = conn.cursor()
c.execute("SELECT exhume_attempts FROM graves WHERE slug='google-reader'")
row = c.fetchone()
attempts = json.loads(row[0]) if row and row[0] else []
for a in attempts:
    text = a.get("text", "")
    t = text.lower().strip()
    print("Len:", len(t))
    matches = [m for m in BAD_MARKERS if m in t[:800]]
    print("Bad matches:", matches)
    print("usable():", usable(text))
    print("Text repr:\n", repr(text))
