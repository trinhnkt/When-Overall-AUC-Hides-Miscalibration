"""C3: acronyms in the body (Introduction to the last reference), first use vs first '(ACR)' definition. Read-only."""
import re
import sys

from msedit import dump

sys.stdout.reconfigure(encoding="utf-8")
lines = dump()
start = next(i for i, l in enumerate(lines) if l.endswith("I. INTRODUCTION"))
end = next(i for i, l in enumerate(lines) if l.endswith("] REFERENCES") or l.endswith("] References"))
body = "\n".join(l for l in lines[start:end] if l.startswith("[P"))
seen = {}
for m in re.finditer(r"\b[A-Z][A-Za-z]*[A-Z]{1,}[a-z]?s?\b|\b[A-Z]{2,}s?\b", body):
    tok = m.group(0).rstrip("s")
    if len(tok) < 2 or tok in seen or tok.isdigit():
        continue
    seen[tok] = m.start()
print(f"{'token':10} first-use  defined-as-(token)  context")
for tok, pos in sorted(seen.items(), key=lambda kv: kv[1]):
    d = body.find(f"({tok})")
    d2 = body.find(f"({tok}s)")
    d = d if d >= 0 else d2
    if d >= 0 and d <= pos + 3:
        continue
    ctx = body[max(0, pos - 45):pos + 45].replace("\n", " ")
    print(f"{tok:10} {pos:9} {d:18}  …{ctx}…")
print()
for i, l in enumerate(lines):
    if re.search(r"\] (Acknowledgment|Funding|Conflict of Interest)", l):
        print(l[:60], "|", lines[i + 1][:500])
