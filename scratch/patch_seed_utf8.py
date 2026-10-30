with open("seed_redig.py", "r", encoding="utf-8") as f:
    content = f.read()

target = 'import argparse\nimport asyncio'
replacement = '''import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import asyncio'''

assert target in content, "target not found in seed_redig.py"
content = content.replace(target, replacement)

with open("seed_redig.py", "w", encoding="utf-8") as f:
    f.write(content)

print("seed_redig.py updated with utf-8 reconfigure!")

