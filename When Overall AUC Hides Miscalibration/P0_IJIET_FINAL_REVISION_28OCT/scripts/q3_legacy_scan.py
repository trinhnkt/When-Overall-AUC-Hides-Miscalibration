"""Review question 3: list every remaining occurrence of T-KT without 'masked', Table A1/A3/A4, archived, final checkpoint,
full history, sparsification, regression in the living blind manuscript, with its paragraph or table row."""
import re
import sys

from msedit import dump

PATTERNS = {
    "T-KT not followed by 'masked'": r"T-KT(?! masked)",
    "unmasked": r"[Uu]nmasked",
    "archived": r"[Aa]rchived",
    "final checkpoint / final-epoch / final/": r"final[ -]checkpoint|final-epoch|final/|final ×|Final ×|final checkpoint",
    "full history": r"full[ -]history|best/full",
    "sparsification / regression": r"sparsification|regression",
}
sys.stdout.reconfigure(encoding="utf-8")
lines = dump()
for name, pat in PATTERNS.items():
    print(f"\n## {name}")
    for line in lines:
        for m in re.finditer(pat, line):
            a = max(0, m.start() - 70)
            print(f"{line[:7].strip():8} …{line[a:m.end() + 70]}…")
