"""C3: list front-matter and licence lines in IJIET_template.doc and print Reference [21] from the three manuscripts."""
from __future__ import annotations

import re
import sys

from msedit import INNER, dump

TEMPLATE = INNER / "P0_IJIET_FINAL_CORRECTION_2026" / "artifact_final" / "07_submission" / "IJIET_template.doc"
PATTERN = re.compile(r"(?i)copyright|creative commons|cc by|licen[cs]e|received|revised|accepted|doi|volume|vol\.|no\.|reference")


def template_lines() -> list[str]:
    raw = TEMPLATE.read_bytes()
    texts = [raw.decode("utf-16-le", errors="ignore"), raw.decode("cp1252", errors="ignore")]
    lines: list[str] = []
    for text in texts:
        for chunk in re.split(r"[\r\n\x07\x0b\x0c]+", text):
            chunk = "".join(ch for ch in chunk if ch.isprintable()).strip()
            if 8 <= len(chunk) <= 600 and sum(c.isalpha() for c in chunk) > 0.6 * len(chunk.replace(" ", "")) and PATTERN.search(chunk):
                if chunk not in lines:
                    lines.append(chunk)
    return lines


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("TEMPLATE", TEMPLATE.name, TEMPLATE.stat().st_size)
    for line in template_lines():
        print("T|", line)
    for line in dump():
        if re.match(r"\[P\d+\]\s*\[2[01]\]", line) or "37673" in line or "16946" in line:
            print("M|", line)
