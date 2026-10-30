with open("scripts/metrics.py", "r", encoding="utf-8") as f:
    content = f.read()

target = 'import asyncio\nimport json'
replacement = '''import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import asyncio
import json'''

if target in content:
    content = content.replace(target, replacement)
    with open("scripts/metrics.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("scripts/metrics.py updated with utf-8 reconfigure!")
else:
    print("target not found")

