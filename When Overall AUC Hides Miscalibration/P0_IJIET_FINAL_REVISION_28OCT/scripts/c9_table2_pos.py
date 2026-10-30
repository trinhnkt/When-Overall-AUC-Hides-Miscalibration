"""Review item 7, Table 2: add a "Positional encoding" row (DKT none; T-KT masked none, protocol_v2.TKTc; simpleKT cosine,
pykt.models.simplekt.CosinePositionalEmbedding, pykt-toolkit 0.0.38). No number changed; new row red. Dry run unless --write."""
import sys
from msedit import W, apply, fill_table, mark_red, table_after, table_rows, text_of

NEW = ["Positional encoding", "None (recurrent)", "None (causal mask only)", "Cosine (pyKT)"]

def edit(body, path):
    rows = table_rows(body, "Table 2.")
    if any(r[0].strip() == NEW[0] for r in rows):
        raise SystemExit("row already present")
    k = [i for i, r in enumerate(rows) if r[0].strip() == "Attention heads"]
    if len(k) != 1:
        raise SystemExit("anchor row not found")
    data = rows[1:]
    data.insert(k[0], NEW)          # rows[0] is the header, so index k[0] puts it right after 'Attention heads'
    fill_table(body, "Table 2.", None, rows[0], data)
    _, tbl = table_after(body, "Table 2.")
    for tr in tbl.findall(W + "tr"):
        if text_of(tr.findall(W + "tc")[0]).strip() == NEW[0]:
            for run in tr.iter(W + "r"):
                mark_red(run)

if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
