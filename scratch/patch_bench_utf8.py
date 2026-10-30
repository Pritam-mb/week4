with open("benchmark.py", "r", encoding="utf-8") as f:
    content = f.read()

target = 'import sys\nfrom pathlib import Path'
replacement = '''import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path'''

assert target in content, "target not found in benchmark.py"
content = content.replace(target, replacement)

with open("benchmark.py", "w", encoding="utf-8") as f:
    f.write(content)

print("benchmark.py updated with utf-8 reconfigure!")

