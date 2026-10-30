"""Table 2, Positional encoding / simpleKT: 'Cosine (pyKT)' -> 'As in pyKT', because the pyKT version used for the runs
is not recorded (requirements-lock points to a local third_party copy that is not in the workspace). Red. Dry run unless --write."""
import sys
from msedit import W, apply, mark_red, table_after, text_of

def edit(body, path):
    _, tbl = table_after(body, "Table 2.")
    hits = 0
    for tr in tbl.findall(W + "tr"):
        tcs = tr.findall(W + "tc")
        if text_of(tcs[0]).strip() == "Positional encoding":
            ts = list(tcs[3].iter(W + "t"))
            if "".join(t.text or "" for t in ts) != "Cosine (pyKT)":
                raise SystemExit("unexpected cell text")
            ts[0].text = "As in pyKT"
            for t in ts[1:]:
                t.text = ""
            mark_red(ts[0].getparent())
            hits += 1
    if hits != 1:
        raise SystemExit(f"row hits {hits}")

if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
