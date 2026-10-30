"""Unit tests for the 21/10 protocol additions. Synthetic data only."""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from src.ece_uncertainty import cluster_bootstrap_diff, size_matched_contrast
from src.protocol_v2 import TKTc, chunk_model_probs, pad_index, predict_windowed
from src.xes_events import (
    EventMeanEncoder,
    assert_one_label,
    prediction_row,
    sequence_probs,
    timestamps_non_decreasing,
    train_frequency,
)


def _tokens(n_kcs=6, length=8, seed=0):
    rng = np.random.default_rng(seed)
    kcs = rng.integers(0, n_kcs, size=length).tolist()
    ys = rng.integers(0, 2, size=length).tolist()
    tokens = [2 * k + y for k, y in zip(kcs, ys)]
    return kcs, ys, tokens


def test_ut_a1_past_predictions_ignore_current_label():
    torch.manual_seed(0)
    n_kcs = 6
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    kcs, ys, tokens = _tokens()
    t = 4
    flipped = tokens.copy()
    flipped[t] = 2 * kcs[t] + (1 - ys[t])
    base = chunk_model_probs(model, tokens, kcs, "cpu")
    alt = chunk_model_probs(model, flipped, kcs, "cpu")
    # Prediction for row i (i >= 1) is base[i - 1], which reads tokens before i.
    for row in range(1, t + 1):
        assert abs(base[row - 1] - alt[row - 1]) <= 1e-6


def test_ut_a2_future_labels_do_not_change_current_prediction():
    torch.manual_seed(1)
    n_kcs = 6
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    kcs, ys, tokens = _tokens(seed=1)
    t = 3
    flipped = tokens.copy()
    for i in range(t + 1, len(tokens)):
        flipped[i] = 2 * kcs[i] + (1 - ys[i])
    base = chunk_model_probs(model, tokens, kcs, "cpu")
    alt = chunk_model_probs(model, flipped, kcs, "cpu")
    assert abs(base[t - 1] - alt[t - 1]) <= 1e-6


def test_ut_a3_prefix_matches_masked_full_chunk():
    torch.manual_seed(2)
    n_kcs = 6
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1).eval()
    kcs, _, tokens = _tokens(seed=2)
    t = 5
    prefix = torch.tensor([tokens[:t]], dtype=torch.long)
    full = torch.tensor([tokens], dtype=torch.long)
    with torch.no_grad():
        p_prefix = model(prefix)[0, -1, kcs[t]]
        p_full = model(full)[0, t - 1, kcs[t]]
    assert abs(float(p_prefix) - float(p_full)) <= 1e-5


def test_ut_a4_trailing_pad_does_not_change_valid_positions():
    torch.manual_seed(3)
    n_kcs = 6
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1).eval()
    kcs, _, tokens = _tokens(seed=3)
    pad = pad_index(n_kcs)
    padded = tokens + [pad] * 20
    x0 = torch.tensor([tokens], dtype=torch.long)
    x1 = torch.tensor([padded], dtype=torch.long)
    with torch.no_grad():
        a = model(x0)[0]
        b = model(x1)[0, : len(tokens)]
    assert torch.allclose(a, b, atol=1e-5)


def test_ut_a5_target_of_position_i_is_the_next_row():
    kcs, _, tokens = _tokens(length=5, seed=4)
    # KTDataset stores features[:-1] and kcs[1:]. Position i predicts row i+1.
    features = tokens[:-1]
    targets = kcs[1:]
    assert len(features) == len(targets)
    for i, kc in enumerate(targets):
        assert kc == kcs[i + 1]


def test_ut_a6_short_fit_loss_is_finite_and_falls():
    torch.manual_seed(5)
    n_kcs = 4
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = nn.BCELoss()
    losses = []
    fixed = [_tokens(n_kcs=n_kcs, length=6, seed=100 + i) for i in range(16)]
    for step in range(80):
        kcs, ys, tokens = fixed[step % 16]
        x = torch.tensor([tokens[:-1]], dtype=torch.long)
        target_kc = torch.tensor(kcs[1:])
        target_y = torch.tensor(ys[1:], dtype=torch.float)
        pred = model(x)[0, torch.arange(len(target_kc)), target_kc]
        loss = loss_fn(pred, target_y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    assert np.isfinite(losses).all()
    assert float(np.mean(losses[-10:])) < float(np.mean(losses[:10]))


def test_ut_a7_previous_label_changes_the_prediction():
    torch.manual_seed(6)
    n_kcs = 6
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    kcs, ys, tokens = _tokens(seed=6)
    t = 4
    flipped = tokens.copy()
    flipped[t - 1] = 2 * kcs[t - 1] + (1 - ys[t - 1])
    base = chunk_model_probs(model, tokens, kcs, "cpu")
    alt = chunk_model_probs(model, flipped, kcs, "cpu")
    assert abs(base[t - 1] - alt[t - 1]) > 1e-6


def test_ut_c1_deepcopy_is_not_a_live_reference():
    torch.manual_seed(7)
    model = TKTc(4, d=16, n_heads=4, n_layers=1)
    live = model.state_dict()
    frozen = copy.deepcopy(model.state_dict())
    with torch.no_grad():
        model.embed.weight.add_(1.0)
    assert torch.equal(live["embed.weight"], model.state_dict()["embed.weight"])
    assert not torch.equal(frozen["embed.weight"], model.state_dict()["embed.weight"])


def test_ut_w1_and_w2_chunk_matches_and_counts_no_history():
    torch.manual_seed(8)
    n_kcs = 5
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    rows = []
    for user, start in ((1, 0), (2, 10)):
        for i in range(5):
            rows.append({
                "user_id": user,
                "timestamp": start + i,
                "kc_id": i % n_kcs,
                "correct": i % 2,
            })
    frame = pd.DataFrame(rows)
    kc_map = {i: i for i in range(n_kcs)}
    scored = predict_windowed(model, frame, kc_map, "cpu", window=3, mode="chunk")
    no_hist = [row for row in scored if row[4] == 1]
    # Two users, window 3: rows 0 and 3 of each user start a chunk. 4 flags.
    assert len(no_hist) == 4
    assert all(row[5] != row[5] for row in no_hist)  # NaN
    used = [row for row in scored if row[4] == 0]
    assert used
    by_user = frame.groupby("user_id", sort=True)
    for uid, group in by_user:
        kcs = [kc_map[k] for k in group["kc_id"].tolist()]
        ys = [int(v) for v in group["correct"].tolist()]
        tokens = [2 * k + y for k, y in zip(kcs, ys)]
        user_rows = [row for row in scored if row[1] == uid and row[4] == 0]
        for row in user_rows:
            i = row[2]
            start = (i // 3) * 3
            manual = chunk_model_probs(model, tokens[start:i + 1], kcs[start:i + 1], "cpu")
            assert abs(manual[-1] - row[5]) <= 1e-5


def test_size_matched_contrast_on_identical_clusters_is_near_zero():
    rng = np.random.default_rng(9)
    clusters = []
    for _ in range(40):
        y = rng.integers(0, 2, size=30)
        p = np.full(30, 0.5)
        clusters.append((y, p))
    sparse_y = np.concatenate([clusters[i][0] for i in range(4)])
    sparse_p = np.concatenate([clusters[i][1] for i in range(4)])
    row = size_matched_contrast(sparse_y, sparse_p, clusters, rng, n_draws=30, n_bins=15)
    assert abs(row["size_matched_diff"]) < 0.05
    boot = cluster_bootstrap_diff(clusters[:8], clusters, rng, n_boot=8, n_inner=4)
    assert boot["n_used"] > 0
    assert boot["n_empty_or_invalid"] == 0


def test_ut_b_event_checks():
    torch.manual_seed(10)
    model = EventMeanEncoder(n_kcs=5, d=8)
    events = [
        {"uid": "a", "event_idx": 0, "qid": 1, "kcs": [0, 1], "y": 1, "timestamp": 1, "split": "train"},
        {"uid": "a", "event_idx": 1, "qid": 2, "kcs": [2], "y": 0, "timestamp": 2, "split": "train"},
        {"uid": "b", "event_idx": 0, "qid": 3, "kcs": [0, 0], "y": 1, "timestamp": 1, "split": "test"},
    ]
    assert_one_label(events)
    assert timestamps_non_decreasing(events)
    freq = train_frequency(events)
    assert freq[0] == 1  # repeated KC inside one event counts once; test event excluded
    assert freq[2] == 1
    base = sequence_probs(model, events[:2])
    swapped = [dict(events[0], kcs=[1, 0]), events[1]]
    alt = sequence_probs(model, swapped)
    assert base[1] == alt[1]
    changed = [events[0], dict(events[1], y=1)]
    # Label of event 1 is not in the state used to score event 1.
    assert sequence_probs(model, events[:2])[1] == sequence_probs(model, changed)[1]
    # It is in the state used to score a following event.
    follow = events[:2] + [{"uid": "a", "event_idx": 2, "qid": 9, "kcs": [3], "y": 0, "timestamp": 3, "split": "test"}]
    follow_alt = changed + [follow[2]]
    assert sequence_probs(model, follow)[2] != sequence_probs(model, follow_alt)[2]
    row = prediction_row(events[0], 0, base[0][0])
    assert row["uid"] == "a" and row["y"] == 1 and row["qid"] == 1
