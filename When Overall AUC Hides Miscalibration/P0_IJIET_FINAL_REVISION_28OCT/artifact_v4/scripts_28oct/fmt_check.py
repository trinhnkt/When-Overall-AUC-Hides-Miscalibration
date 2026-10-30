"""List paragraphs whose HEAD version had italic, bold, sub/superscript runs that the current file lacks."""
from __future__ import annotations

import io
import subprocess
import sys
import zipfile

from lxml import etree

from msedit import INNER, PATHS, W, text_of

KEYS = ("i", "b", "vertAlign")


def styled(para) -> list[str]:
    acc: dict[str, str] = {}
    for r in para.iter(W + "r"):
        pr = r.find(W + "rPr")
        if pr is None:
            continue
        t = "".join(x.text or "" for x in r.iter(W + "t")).replace(" ", "")
        for k in KEYS:
            el = pr.find(W + k)
            if el is not None and el.get(W + "val") not in ("0", "false", "baseline"):
                tag = k + (":" + el.get(W + "val") if el.get(W + "val") else "")
                acc[tag] = acc.get(tag, "") + t
    return [f"{k}={v}" for k, v in sorted(acc.items()) if v]


def paras(root):
    return {text_of(p)[:60]: p for p in root.iter(W + "p") if text_of(p).strip()}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    rel = PATHS[0].relative_to(INNER.parent).as_posix()
    blob = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, cwd=INNER.parent, check=True).stdout
    head = etree.fromstring(zipfile.ZipFile(io.BytesIO(blob)).read("word/document.xml"))
    cur = etree.fromstring(zipfile.ZipFile(PATHS[0]).read("word/document.xml"))
    hp = paras(head)
    lost = 0
    for p in cur.iter(W + "p"):
        key = text_of(p)[:30]
        match = [hp[k] for k in hp if k.startswith(key)] if len(key.strip()) >= 25 else []
        if not match:
            continue
        old, new = styled(match[0]), styled(p)
        missing = [s for s in old if s not in new]
        if missing:
            lost += 1
            print(f"LOST in {key!r}: {missing}")
    print(f"paragraphs with lost formatting: {lost}")


if __name__ == "__main__":
    main()
