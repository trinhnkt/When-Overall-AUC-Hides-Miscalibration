import re
import sys
import zipfile

from lxml import etree

from c3_template_compare import TEMPLATE
from msedit import PATHS, W, text_of

sys.stdout.reconfigure(encoding="utf-8")
for label, path in (("TEMPLATE", TEMPLATE), ("MANUSCRIPT", PATHS[1])):
    z = zipfile.ZipFile(path)
    print("==", label)
    for name in z.namelist():
        if re.fullmatch(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml", name):
            root = etree.fromstring(z.read(name))
            for p in root.iter(W + "p"):
                t = text_of(p)
                if "Copyright" in t or "Creative Commons" in t or "Manuscript received" in t:
                    anc = [etree.QName(a).localname for a in p.iterancestors()][:5]
                    ppr = p.find(W + "pPr")
                    sty = p.find(f"{W}pPr/{W}pStyle")
                    print(f"  {name} ancestors={anc} style={sty.get(W + 'val') if sty is not None else None}")
                    print("     ", t[:260])
    hdrs = [n for n in z.namelist() if re.fullmatch(r"word/(header|footer)\d*\.xml", n)]
    print("  header/footer parts:", hdrs)
    for n in hdrs:
        print("   ", n, repr("".join(t.text or "" for t in etree.fromstring(z.read(n)).iter(W + "t"))[:200]))
    rels = z.read("word/_rels/document.xml.rels").decode()
    print("  hyperlinks in rels:", re.findall(r'Target="(https://creativecommons[^"]*)"', rels))
