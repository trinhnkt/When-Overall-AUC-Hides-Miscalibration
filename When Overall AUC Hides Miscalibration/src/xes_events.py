"""Question-level XES3G5M event checks. One question attempt is one step.

This does not retrain DKT. It checks the event table the supplementary
round requires before any XES model is scored again.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn


def event_token(kc: int, y: int) -> int:
    return 2 * int(kc) + int(y)


class EventMeanEncoder(nn.Module):
    """Mean of per-KC response embeddings, then a linear head over KC ids."""

    def __init__(self, n_kcs: int, d: int = 8):
        super().__init__()
        self.n_kcs = n_kcs
        self.embed = nn.Embedding(2 * n_kcs + 1, d)
        self.fc = nn.Linear(d, n_kcs)

    def event_vector(self, kcs, y: int) -> torch.Tensor:
        tokens = torch.tensor([event_token(c, y) for c in kcs], dtype=torch.long)
        return self.embed(tokens).mean(dim=0)

    def probs_from_state(self, state: torch.Tensor, kcs) -> dict:
        logits = self.fc(state)
        probs = torch.sigmoid(logits)
        return {int(c): float(probs[int(c)].item()) for c in kcs}


def sequence_probs(model: EventMeanEncoder, events):
    """events: list of dicts with keys kcs, y. State for event t is the sum of earlier events."""
    state = torch.zeros(model.embed.embedding_dim)
    rows = []
    for event in events:
        rows.append(model.probs_from_state(state, event["kcs"]))
        state = state + model.event_vector(event["kcs"], event["y"])
    return rows


def assert_one_label(events) -> None:
    for event in events:
        if "y" not in event or event["y"] not in (0, 1):
            raise AssertionError("each event needs exactly one binary label")


def train_frequency(events) -> dict:
    """Count each KC at most once per training event. Test events do not count."""
    freq = defaultdict(int)
    for event in events:
        if event.get("split") != "train":
            continue
        for kc in set(int(c) for c in event["kcs"]):
            freq[kc] += 1
    return dict(freq)


def timestamps_non_decreasing(events) -> bool:
    by_user = defaultdict(list)
    for event in events:
        by_user[event["uid"]].append(event["timestamp"])
    for stamps in by_user.values():
        if any(b < a for a, b in zip(stamps, stamps[1:])):
            return False
    return True


def prediction_row(event, kc, p) -> dict:
    return {
        "uid": event["uid"],
        "event_idx": event["event_idx"],
        "qid": event["qid"],
        "kc": kc,
        "y": event["y"],
        "p": p,
    }


class DKTEvent(nn.Module):
    """One question attempt is one LSTM step. P-6.4.

    out[:, t] predicts every KC of event t + 1 from the state after event t.
    """

    def __init__(self, n_kcs: int, d: int = 64, h: int = 128):
        super().__init__()
        self.n_kcs = n_kcs
        self.pad = 2 * n_kcs
        self.bag = nn.EmbeddingBag(
            2 * n_kcs + 1, d, mode="mean", padding_idx=self.pad
        )
        self.lstm = nn.LSTM(d, h, batch_first=True)
        self.fc = nn.Linear(h, n_kcs)

    def forward(self, tok_sets: torch.Tensor) -> torch.Tensor:
        batch, seq, width = tok_sets.shape
        embedded = self.bag(tok_sets.reshape(batch * seq, width)).reshape(batch, seq, -1)
        hidden, _ = self.lstm(embedded)
        return torch.sigmoid(self.fc(hidden))


def parse_kc_set(cell: str) -> list[int]:
    """Unique KCs in first-seen order. A repeated KC inside one event counts once."""
    found = []
    for part in str(cell).split("_"):
        part = part.strip()
        if not part or part == "-1":
            continue
        kc = int(part)
        if kc not in found:
            found.append(kc)
    return found


def iter_sequence_events(row, source: str):
    """Expand one released sequence into question attempts.

    Equal timestamps keep the order already stored in the sequence.
    That is the tie break.
    """
    questions = str(row.questions).split(",")
    concepts = str(row.concepts).split(",")
    responses = str(row.responses).split(",")
    timestamps = str(row.timestamps).split(",")
    width = len(questions)
    if not (len(concepts) == width and len(responses) == width and len(timestamps) == width):
        raise ValueError(f"uid {row.uid} has unequal sequence fields")
    order = []
    for i in range(width):
        if questions[i].strip() in {"", "-1"}:
            continue
        if int(timestamps[i]) < 0:
            continue
        order.append(i)
    order.sort(key=lambda i: (int(timestamps[i]), i))
    for event_idx, i in enumerate(order):
        kcs = parse_kc_set(concepts[i])
        if not kcs:
            raise ValueError(f"uid {row.uid} event {event_idx} has no KC")
        yield {
            "uid": int(row.uid),
            "event_idx": event_idx,
            "qid": int(questions[i]),
            "kcs": kcs,
            "timestamp": int(timestamps[i]),
            "y": int(responses[i]),
            "source": source,
            "split": source,
            "fold": int(getattr(row, "fold")),
        }


def count_question_ids(paths) -> int:
    import pandas as pd

    found = set()
    for path in paths:
        for chunk in pd.read_csv(path, usecols=["questions"], chunksize=2000):
            for cell in chunk["questions"].dropna():
                for qid in str(cell).split(","):
                    qid = qid.strip()
                    if qid and qid != "-1":
                        found.add(qid)
    return len(found)
