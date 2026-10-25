"""Event-level XES checks. One question attempt is one event.

Synthetic sequences only. These tests do not score the legacy KC-row file
and they do not train a model.
"""
from __future__ import annotations

import torch

from src.xes_events import (
    DKTEvent,
    assert_one_label,
    parse_kc_set,
    timestamps_non_decreasing,
    train_frequency,
)


def _event(uid, idx, qid, kcs, y, timestamp, split="train"):
    return {
        "uid": uid,
        "event_idx": idx,
        "qid": qid,
        "kcs": list(kcs),
        "y": int(y),
        "timestamp": int(timestamp),
        "split": split,
        "response_id": (uid, int(timestamp), int(qid)),
    }


def _score(model: DKTEvent, events: list[dict]) -> list[dict]:
    """p(t, c) for every KC of event t, from events strictly before t."""
    if not events:
        return []
    width = max(len(event["kcs"]) for event in events)
    tokens = []
    for event in events:
        ids = [2 * int(kc) + int(event["y"]) for kc in event["kcs"]]
        ids.extend([model.pad] * (width - len(ids)))
        tokens.append(ids)
    batch = torch.tensor([tokens], dtype=torch.long)
    with torch.no_grad():
        hidden = model(batch)[0]
    rows = []
    for t, event in enumerate(events):
        if t == 0:
            rows.append({})
            continue
        state = hidden[t - 1]
        rows.append({int(kc): float(state[int(kc)].item()) for kc in event["kcs"]})
    return rows


def _history_then_response(n_kcs: int, kcs: list[int], y: int):
    """One prior event, then the response under test, then one later event."""
    torch.manual_seed(0)
    model = DKTEvent(n_kcs=8, d=16, h=16)
    model.eval()
    base = [
        _event(1, 0, 100, [0], 1, 1),
        _event(1, 1, 200, kcs, y, 2),
        _event(1, 2, 300, [3], 0, 3),
    ]
    flipped = [dict(base[0]), dict(base[1], y=1 - y), dict(base[2])]
    return model, base, flipped


def test_parse_kc_set_counts_a_repeated_kc_once():
    assert parse_kc_set("4_4_9_-1") == [4, 9]


def test_one_label_and_learner_disjoint_and_time_order():
    events = [
        _event(1, 0, 10, [0], 1, 5, "train"),
        _event(1, 1, 11, [1, 2], 0, 5, "train"),
        _event(2, 0, 10, [0], 1, 9, "test"),
    ]
    assert_one_label(events)
    train = {e["uid"] for e in events if e["split"] == "train"}
    test = {e["uid"] for e in events if e["split"] == "test"}
    assert train.isdisjoint(test)
    assert timestamps_non_decreasing(events)
    decreasing = [_event(1, 0, 11, [1], 0, 9), _event(1, 1, 10, [0], 1, 5)]
    assert timestamps_non_decreasing(decreasing) is False


def test_train_frequency_is_train_only_and_once_per_event():
    events = [
        _event(1, 0, 10, [0, 0, 1], 1, 1, "train"),
        _event(1, 1, 11, [1], 0, 2, "test"),
    ]
    freq = train_frequency(events)
    assert freq == {0: 1, 1: 1}


def test_flip_outcome_leaves_every_kc_probability_unchanged():
    for kcs, y in (
        ([1], 1),
        ([1, 2], 0),
        ([1, 2, 4], 1),
    ):
        model, base, flipped = _history_then_response(8, kcs, y)
        before = _score(model, base)[1]
        after = _score(model, flipped)[1]
        assert set(before) == set(kcs)
        for kc in kcs:
            assert abs(before[kc] - after[kc]) <= 1e-6


def test_previous_outcome_can_change_the_next_response():
    model, base, flipped = _history_then_response(8, [1, 2], 1)
    later_base = _score(model, base)[2]
    later_flip = _score(model, flipped)[2]
    assert abs(later_base[3] - later_flip[3]) > 1e-6


def test_same_question_id_at_a_later_time_is_a_new_event():
    torch.manual_seed(1)
    model = DKTEvent(n_kcs=6, d=16, h=16)
    model.eval()
    events = [
        _event(1, 0, 7, [0, 1], 1, 10),
        _event(1, 1, 8, [2], 0, 20),
        _event(1, 2, 7, [0, 1], 0, 30),
    ]
    assert len({e["response_id"] for e in events}) == 3
    flipped = [dict(events[0], y=0), events[1], events[2]]
    base = _score(model, events)
    alt = _score(model, flipped)
    for kc in (0, 1):
        assert abs(base[0].get(kc, 0.0) - alt[0].get(kc, 0.0)) <= 1e-6
    assert abs(base[2][0] - alt[2][0]) > 1e-6


def test_window_concatenation_does_not_repeat_a_response():
    window_a = [
        _event(1, 0, 1, [0], 1, 10),
        _event(1, 1, 2, [1], 0, 20),
    ]
    window_b = [
        _event(1, 0, 3, [2], 1, 30),
        _event(1, 1, 4, [0, 1], 0, 40),
    ]
    joined = []
    for window in (window_a, window_b):
        joined.extend(window)
    for i, event in enumerate(joined):
        event["event_idx"] = i
    ids = [event["response_id"] for event in joined]
    assert len(ids) == len(set(ids)) == 4
    # The first event of the second window is scored once, from both earlier events.
    torch.manual_seed(2)
    model = DKTEvent(n_kcs=4, d=8, h=8)
    model.eval()
    scored = _score(model, joined)
    assert set(scored[2]) == {2}


def test_trailing_pad_steps_do_not_change_earlier_predictions():
    torch.manual_seed(3)
    model = DKTEvent(n_kcs=4, d=8, h=8)
    model.eval()
    events = [
        _event(1, 0, 1, [0], 1, 1),
        _event(1, 1, 2, [1, 2], 0, 2),
    ]
    width = 2
    real = []
    for event in events:
        ids = [2 * kc + event["y"] for kc in event["kcs"]]
        ids.extend([model.pad] * (width - len(ids)))
        real.append(ids)
    pad_step = [model.pad] * width
    x0 = torch.tensor([real], dtype=torch.long)
    x1 = torch.tensor([real + [pad_step, pad_step]], dtype=torch.long)
    with torch.no_grad():
        a = model(x0)[0]
        b = model(x1)[0, : len(real)]
    assert torch.allclose(a, b, atol=1e-5)
