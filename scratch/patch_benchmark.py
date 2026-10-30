with open("benchmark.py", "r", encoding="utf-8") as f:
    content = f.read()

old_bench = '''                text = res.get("text", "") or ""
                ok   = usable(text)
                chars = len(text)
                err  = res.get("error") or ""
                fields_filled = res.get("fields_filled", 0)'''

new_bench = '''                text = res.get("text", "") or ""
                fields_filled = res.get("fields_filled", 0)
                ok   = usable(text, fields_filled)
                chars = len(text)
                err  = res.get("error") or ""'''

assert old_bench in content, "old_bench not found"
content = content.replace(old_bench, new_bench)

with open("benchmark.py", "w", encoding="utf-8") as f:
    f.write(content)

print("benchmark.py patched successfully!")

