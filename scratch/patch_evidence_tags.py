with open("pipeline.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace evidence formatting in ask_eulogist
old_eulogist_ev = '''    # Build evidence tags for the prompt
    if evidence:
        ev_lines = []
        for ev in evidence:
            eid = ev.get("evidence_id", "E???")
            method = ev.get("method", "unknown")
            ok = ev.get("ok", False)
            chars = ev.get("chars", 0)
            ev_lines.append(f"<evidence id=\\"{eid}\\" method=\\"{method}\\" usable=\\"{ok}\\" chars=\\"{chars}\\">")
            ev_lines.append(f"  Snapshot: {ev.get('ts', '?')}")
            ev_lines.append(f"  URL: {ev.get('link', '?')}")
            if ev.get("error"):
                ev_lines.append(f"  Error: {ev['error']}")
            ev_lines.append("</evidence>")
        evidence_text = "\\n".join(ev_lines)
    else:
        evidence_text = "<evidence id=\\"E000\\" method=\\"none\\" usable=\\"false\\" chars=\\"0\\">No usable evidence captured.</evidence>"'''

new_eulogist_ev = '''    # Build evidence tags for the prompt
    if evidence:
        ev_lines = []
        for ev in evidence:
            eid = ev.get("evidence_id", "E???")
            method = ev.get("method", "unknown")
            ok = ev.get("status") == "ok" or ev.get("ok", False)
            chars = ev.get("chars", 0)
            snippet = (ev.get("text") or "").strip()[:1000]
            ev_lines.append(f"<evidence id=\\"{eid}\\" method=\\"{method}\\" usable=\\"{ok}\\" chars=\\"{chars}\\">")
            ev_lines.append(f"  Snapshot: {ev.get('ts', '?')}")
            ev_lines.append(f"  URL: {ev.get('link', '?')}")
            if snippet:
                ev_lines.append(f"  Text: {snippet}")
            if ev.get("error"):
                ev_lines.append(f"  Error: {ev['error']}")
            ev_lines.append("</evidence>")
        evidence_text = "\\n".join(ev_lines)
    else:
        evidence_text = "<evidence id=\\"E000\\" method=\\"none\\" usable=\\"false\\" chars=\\"0\\">No usable evidence captured.</evidence>"'''

assert old_eulogist_ev in content, "old_eulogist_ev not found"
content = content.replace(old_eulogist_ev, new_eulogist_ev)

# Replace evidence formatting in fact_check_eulogy
old_fc_ev = '''    # Build evidence block for fact-checker
    if evidence:
        ev_lines = []
        for ev in evidence:
            eid = ev.get("evidence_id", "E???")
            ok = ev.get("ok", False)
            chars = ev.get("chars", 0)
            ev_lines.append(f"<evidence id=\\"{eid}\\" usable=\\"{ok}\\" chars=\\"{chars}\\">")
            ev_lines.append(f"  Snapshot: {ev.get('ts', '?')}")
            ev_lines.append(f"  URL: {ev.get('link', '?')}")
            if ev.get("error"):
                ev_lines.append(f"  Error: {ev['error']}")
            ev_lines.append("</evidence>")
        evidence_text = "\\n".join(ev_lines)
    else:
        evidence_text = "<evidence id=\\"E000\\" usable=\\"false\\" chars=\\"0\\">No usable evidence captured.</evidence>"'''

new_fc_ev = '''    # Build evidence block for fact-checker
    if evidence:
        ev_lines = []
        for ev in evidence:
            eid = ev.get("evidence_id", "E???")
            ok = ev.get("status") == "ok" or ev.get("ok", False)
            chars = ev.get("chars", 0)
            snippet = (ev.get("text") or "").strip()[:1000]
            ev_lines.append(f"<evidence id=\\"{eid}\\" usable=\\"{ok}\\" chars=\\"{chars}\\">")
            ev_lines.append(f"  Snapshot: {ev.get('ts', '?')}")
            ev_lines.append(f"  URL: {ev.get('link', '?')}")
            if snippet:
                ev_lines.append(f"  Text: {snippet}")
            if ev.get("error"):
                ev_lines.append(f"  Error: {ev['error']}")
            ev_lines.append("</evidence>")
        evidence_text = "\\n".join(ev_lines)
    else:
        evidence_text = "<evidence id=\\"E000\\" usable=\\"false\\" chars=\\"0\\">No usable evidence captured.</evidence>"'''

assert old_fc_ev in content, "old_fc_ev not found"
content = content.replace(old_fc_ev, new_fc_ev)

# Fix REWRITE_PROMPT length rule
content = content.replace("- Keep length 60-120 words", "- Keep length 150-220 words")

with open("pipeline.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Evidence tags patched successfully in pipeline.py!")

