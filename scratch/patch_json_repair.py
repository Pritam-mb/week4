with open("pipeline.py", "r", encoding="utf-8") as f:
    content = f.read()

old_parse = '''def _parse_json_safe(raw: str) -> dict | None:
    cleaned = re.sub(r"`(?:json)?", "", raw).strip().rstrip("").strip()
    match = re.search(r"\\{.*\\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}\\nRaw: {raw[:300]}")
        return None'''

new_parse = '''def _parse_json_safe(raw: str) -> dict | None:
    cleaned = re.sub(r"^```(?:json)?", "", raw.strip()).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\\{.*\\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            if '"claims"' in cleaned:
                last_brace = cleaned.rfind("}")
                if last_brace != -1:
                    repaired = cleaned[:last_brace+1] + "]}"
                    return json.loads(repaired)
        except Exception:
            pass
        logger.warning(f"JSON parse failed\\nRaw: {raw[:300]}")
        return None'''

assert old_parse in content, "old_parse not found"
content = content.replace(old_parse, new_parse)

old_fc_return = '''        if recheck_raw:
            recheck_data = _parse_json_safe(recheck_raw)
            if recheck_data and "claims" in recheck_data:
                unsupported_after = sum(1 for c in recheck_data["claims"] if not c.get("supported", True))

    return {
        "claims": claims,
        "eulogy_verified": eulogy_verified,
        "unsupported_before": unsupported_before,
        "unsupported_after": unsupported_after,
    }'''

new_fc_return = '''        if recheck_raw:
            recheck_data = _parse_json_safe(recheck_raw)
            if recheck_data and "claims" in recheck_data:
                claims = recheck_data["claims"]
                unsupported_after = sum(1 for c in claims if not c.get("supported", True))

    return {
        "claims": claims,
        "eulogy_verified": eulogy_verified,
        "unsupported_before": unsupported_before,
        "unsupported_after": unsupported_after,
    }'''

assert old_fc_return in content, "old_fc_return not found"
content = content.replace(old_fc_return, new_fc_return)

with open("pipeline.py", "w", encoding="utf-8") as f:
    f.write(content)

print("JSON repair and claims update patched successfully!")

