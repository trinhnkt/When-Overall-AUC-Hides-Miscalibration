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
