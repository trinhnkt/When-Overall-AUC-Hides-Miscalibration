#!/usr/bin/env python3
"""B4 gate. UT-B1 through UT-B8, first on 1,000 learners, then on the full release.

Reads question_level only. Does not rebuild events from kc_level.
Equal timestamps keep the original sequence order.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.xes_events import (  # noqa: E402
    DKTEvent,
    assert_one_label,
    iter_sequence_events,
    parse_kc_set,
    prediction_row,
    timestamps_non_decreasing,
    train_frequency,
)

QUESTION = ROOT / "data" / "raw" / "xes3g5m" / "question_level"
TRAIN_PATH = QUESTION / "train_valid_sequences_quelevel.csv"
TEST_PATH = QUESTION / "test_quelevel.csv"
EXPECTED_QUESTIONS = 7652


def read_uids(path: Path) -> list[int]:
    frame = pd.read_csv(path, usecols=["uid"])
    return [int(v) for v in frame["uid"].tolist()]


def expand(path: Path, source: str, keep: set[int] | None) -> list[dict]:
    grouped: dict[int, list] = {}
    for chunk in pd.read_csv(path, chunksize=200):
        for row in chunk.itertuples(index=False):
            uid = int(row.uid)
            if keep is not None and uid not in keep:
                continue
            grouped.setdefault(uid, []).append(row)
    events = []
    for uid, rows in grouped.items():
        windows = []
        for row in rows:
            seq = list(iter_sequence_events(row, source))
            if seq:
                windows.append(seq)
        windows.sort(key=lambda seq: (seq[0]["timestamp"], seq[0]["qid"], seq[0]["event_idx"]))
        flat = [event for seq in windows for event in seq]
        for event_idx, event in enumerate(flat):
            event["event_idx"] = event_idx
            event["uid"] = uid
        events.extend(flat)
    return events


def sequence_through_model(model: DKTEvent, events: list[dict]) -> list[dict]:
    """p for event t comes from the state after events before t."""
    if not events:
        return []
    width = max(len(event["kcs"]) for event in events)
    rows = []
    tokens = []
    for event in events:
        ids = [2 * kc + int(event["y"]) for kc in event["kcs"]]
        ids.extend([model.pad] * (width - len(ids)))
        tokens.append(ids)
    batch = torch.tensor([tokens], dtype=torch.long)
    with torch.no_grad():
        probs = model(batch)[0]
    for t, event in enumerate(events):
        if t == 0:
            rows.append({})
            continue
        state = probs[t - 1]
        rows.append({int(kc): float(state[int(kc)].item()) for kc in event["kcs"]})
    return rows


def check_model_properties(events: list[dict]) -> None:
    torch.manual_seed(0)
    n_kcs = 1 + max(kc for event in events for kc in event["kcs"])
    model = DKTEvent(n_kcs=n_kcs, d=16, h=16)
    model.eval()
    user_events = [event for event in events if event["uid"] == events[0]["uid"]]
    user_events = sorted(user_events, key=lambda event: event["event_idx"])
    if len(user_events) < 3:
        raise AssertionError("sample user needs at least three events")
    base = sequence_through_model(model, user_events)
    swapped = [dict(event) for event in user_events]
    swapped[1] = dict(swapped[1], kcs=list(reversed(swapped[1]["kcs"])))
    alt = sequence_through_model(model, swapped)
    for t in range(1, len(user_events)):
        for kc in user_events[t]["kcs"]:
            if abs(base[t][kc] - alt[t].get(kc, base[t][kc])) > 1e-6:
                raise AssertionError("KC order changed a probability")
    flipped = [dict(event) for event in user_events]
    target = 1
    flipped[target] = dict(flipped[target], y=1 - int(flipped[target]["y"]))
    changed = sequence_through_model(model, flipped)
    for kc in user_events[target]["kcs"]:
        if abs(base[target][kc] - changed[target][kc]) > 1e-6:
            raise AssertionError("current label changed p_t")
    later = target + 1
    moved = False
    for kc in user_events[later]["kcs"]:
        if abs(base[later][kc] - changed[later][kc]) > 1e-6:
            moved = True
    if not moved:
        raise AssertionError("previous label did not change p_{t+1}")


def check_events(events: list[dict], train_uids: set[int], test_uids: set[int], full: bool) -> None:
    assert_one_label(events)
    print("UT-B1 = PASS")
    check_model_properties(events)
    print("UT-B2 = PASS")
    print("UT-B3 = PASS")
    overlap = train_uids & test_uids
    if overlap:
        raise AssertionError(f"{len(overlap)} learners are in train and test")
    seen = set()
    for event in events:
        key = (event["uid"], event["event_idx"])
        if key in seen:
            raise AssertionError(f"duplicate event {key}")
        seen.add(key)
    print("UT-B4 = PASS")
    if not timestamps_non_decreasing(events):
        raise AssertionError("a learner timestamp decreased")
    print("UT-B5 = PASS")
    freq = train_frequency(events)
    expected = {}
    for event in events:
        if event["source"] != "train":
            continue
        for kc in set(event["kcs"]):
            expected[kc] = expected.get(kc, 0) + 1
    if freq != expected:
        raise AssertionError("f_train does not match one count per KC per training event")
    print("UT-B6 = PASS")
    sample = events[0]
    row = prediction_row(sample, sample["kcs"][0], 0.5)
    if row["uid"] != sample["uid"] or row["qid"] != sample["qid"] or row["y"] != sample["y"]:
        raise AssertionError("prediction row is not aligned")
    if row["event_idx"] != sample["event_idx"] or row["kc"] != sample["kcs"][0]:
        raise AssertionError("prediction row dropped the KC")
    print("UT-B7 = PASS")
    questions = {event["qid"] for event in events}
    attachments = sum(len(event["kcs"]) for event in events)
    multi = sum(len(event["kcs"]) > 1 for event in events)
    print(
        f"UT-B8 questions={len(questions)} multi_kc_events={multi} "
        f"events={len(events)} attachments={attachments}"
    )
    if full and len(questions) != EXPECTED_QUESTIONS:
        raise AssertionError(f"question count {len(questions)} is not {EXPECTED_QUESTIONS}")
    print("UT-B8 = PASS")


def folds_are_unique(path: Path) -> dict[int, int]:
    frame = pd.read_csv(path, usecols=["uid", "fold"])
    folded = frame.groupby("uid")["fold"].nunique()
    if int((folded > 1).sum()):
        raise AssertionError("a learner is assigned to more than one fold")
    return {int(uid): int(fold) for uid, fold in frame.drop_duplicates("uid")[["uid", "fold"]].itertuples(index=False)}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    mode = sys.argv[1] if len(sys.argv) > 1 else "sample"
    train_uids = set(read_uids(TRAIN_PATH))
    test_uids = set(read_uids(TEST_PATH))
    folds_are_unique(TRAIN_PATH)
    if mode == "sample":
        chosen = set(sorted(train_uids | test_uids)[:1000])
        events = expand(TRAIN_PATH, "train", chosen) + expand(TEST_PATH, "test", chosen)
        check_events(events, train_uids & chosen, test_uids & chosen, full=False)
        print("B4_SAMPLE = PASS")
        return
    if mode != "full":
        raise SystemExit("use sample or full")
    events = expand(TRAIN_PATH, "train", None) + expand(TEST_PATH, "test", None)
    check_events(events, train_uids, test_uids, full=True)
    print("B4_FULL = PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("UT-B = FAIL")
        print(exc)
        raise
