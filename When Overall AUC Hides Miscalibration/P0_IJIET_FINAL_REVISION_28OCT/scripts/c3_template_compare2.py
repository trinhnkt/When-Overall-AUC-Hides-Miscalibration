import re
import sys

from lxml import etree

from c3_template_compare import TEMPLATE, align_of, root_of
from msedit import PATHS, W, dump, text_of

sys.stdout.reconfigure(encoding="utf-8")
t_root, _ = root_of(TEMPLATE)
paras = list(t_root.find(W + "body").iter(W + "p"))
print("TEMPLATE last paragraphs:")
for p in paras[-4:]:
    print("  ", align_of(p), repr(text_of(p)[:90]))
    jc = p.find(f"{W}pPr/{W}jc")
    for r in p.iter(W + "r"):
        pr = r.find(W + "rPr")
        sz = pr.find(W + "sz").get(W + "val") if pr is not None and pr.find(W + "sz") is not None else None
        print("      run", repr(text_of(r)[:40]), "sz", sz, "hyperlink-in-run" if r.getparent().tag == W + "hyperlink" else "")
        break
sect = [p for p in paras if p.find(f"{W}pPr/{W}sectPr") is not None]
print("paragraphs carrying a section break:", len(sect))
m_root, _ = root_of(PATHS[1])
mp = list(m_root.find(W + "body").iter(W + "p"))
print("MANUSCRIPT last paragraphs:")
for p in mp[-3:]:
    print("  ", align_of(p), repr(text_of(p)[:90]))
lines = dump(PATHS[1])
text = "\n".join(lines)
print("\nECE / DKT definitions in text:")
for pat in (r"[^.]{0,60}\(ECE\)[^.]{0,30}", r"[^.]{0,60}\(DKT\)[^.]{0,30}", r"[^.]{0,60}\(KT\)[^.]{0,20}"):
    for m in re.finditer(pat, text):
        print("   ", m.group(0).strip()[:140])
print("\nFirst body use of ECE and DKT outside the abstract:")
body_text = text[text.find("I. INTRODUCTION"):]
for s in ("ECE", "DKT"):
    m = re.search(rf"[^.]{{0,100}}\b{s}\b[^.]{{0,60}}", body_text)
    print("   ", s, "->", m.group(0).strip() if m else None)
print("\nAcknowledgment / Funding paragraphs:")
for i, l in enumerate(lines):
    if "Acknowledgment" in l[:20] or "Funding" in l[:20]:
        print("   ", lines[i][:80], "|", lines[i + 1][:400])
print("\nAll reference lines with http or Online:")
for l in lines:
    if re.match(r"\[P\d+\] [A-Z“\"]", l) and ("http" in l or "[Online]" in l):
        print("   ", l)
print("\nAI declaration paragraph:")
for l in lines:
    if "Cursor" in l or "ChatGPT" in l:
        print("   ", l[:700])
