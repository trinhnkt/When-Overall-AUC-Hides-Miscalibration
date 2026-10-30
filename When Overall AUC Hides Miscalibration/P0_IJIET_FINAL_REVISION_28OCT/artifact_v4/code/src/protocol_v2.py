"""Protocol additions for the 21/10/2026 supplementary round.

T-KT-c, windowed scoring, and prediction-schema helpers. The local T-KT
class in baseline_runner is unchanged so the old protocol can still be named.
"""
from __future__ import annotations

import torch
import torch.nn as nn


def pad_index(n_kcs: int) -> int:
    """Unused slot in Embedding(2 * n_kcs + 1). Not a real KC-response token."""
    return 2 * n_kcs


class TKTc(nn.Module):
    """Local Transformer with a causal mask and a padding mask.

    Input x[:, i] is the token of row i. The training shift in KTDataset
    already maps position i onto the next row, so this module does not add
    a BOS token and does not shift again.
    """

    def __init__(self, n_kcs: int, d: int = 64, n_heads: int = 4, n_layers: int = 2):
        super().__init__()
        self.n_kcs = n_kcs
        self.embed = nn.Embedding(2 * n_kcs + 1, d, padding_idx=pad_index(n_kcs))
        layer = nn.TransformerEncoderLayer(
            d_model=d, nhead=n_heads, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(
            layer, num_layers=n_layers, enable_nested_tensor=False
        )
        self.fc = nn.Linear(d, n_kcs)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seq = x.size(1)
        ones = torch.ones(seq, seq, dtype=torch.bool, device=x.device)
        causal = torch.triu(ones, diagonal=1)
        pad = x.eq(pad_index(self.n_kcs))
        hidden = self.transformer(
            self.embed(x), mask=causal, src_key_padding_mask=pad
        )
        return torch.sigmoid(self.fc(hidden))


def predict_windowed(model, test_df, kc_map, device, window=200, mode="full"):
    """Score each test row from a bounded history.

    Returns a list of (row_index, user_id, seq_pos, history_len, no_history, p).
    no_history is 1 when the window contains no earlier response. Those rows
    are not part of the primary ECE.
    """
    if mode not in ("full", "chunk", "slide"):
        raise ValueError(mode)
    model.eval()
    frame = test_df.sort_values(["user_id", "timestamp"]) if "timestamp" in test_df.columns else test_df
    out = []
    with torch.no_grad():
        for uid, group in frame.groupby("user_id", sort=True):
            kcs = [kc_map[k] for k in group["kc_id"].tolist()]
            ys = [int(v) for v in group["correct"].tolist()]
            tokens = [2 * k + y for k, y in zip(kcs, ys)]
            indexes = group.index.tolist()
            for i, tok in enumerate(tokens):
                if mode == "chunk":
                    start = (i // window) * window
                elif mode == "slide":
                    start = max(0, i - (window - 1))
                else:
                    start = 0
                hist = tokens[start:i]
                if not hist:
                    out.append((indexes[i], uid, i, 0, 1, float("nan")))
                    continue
                x = torch.tensor([hist], dtype=torch.long, device=device)
                prob = model(x)[0, -1, kcs[i]].item()
                out.append((indexes[i], uid, i, len(hist), 0, float(prob)))
    return out


def chunk_model_probs(model, tokens, kcs, device):
    """Probability of each row after the first, from one KTDataset-style chunk.

    Position i in the model input is token i, and the output at that position
    is the prediction for row i + 1.
    """
    if len(tokens) < 2:
        return []
    model.eval()
    x = torch.tensor([tokens[:-1]], dtype=torch.long, device=device)
    with torch.no_grad():
        pred = model(x)[0]
    return [float(pred[j, kcs[j + 1]].item()) for j in range(len(tokens) - 1)]
