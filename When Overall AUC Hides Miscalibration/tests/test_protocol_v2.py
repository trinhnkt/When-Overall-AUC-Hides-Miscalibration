"""Unit tests for the 21/10 protocol additions. Synthetic data only."""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from src.ece_uncertainty import (
    cluster_bootstrap_diff,
    dense_at_n,
    ece_sweep,
    kumar_squared_ce,
    size_matched_contrast,
)
from src.protocol_v2 import (
    TKTc,
    chunk_model_probs,
    no_history_counts,
    pad_index,
    predict_windowed,
    score_windowed,
)
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


def _prefix_matches_full(model, tokens, kcs, t):
    model.eval()
    prefix = torch.tensor([tokens[:t]], dtype=torch.long)
    full = torch.tensor([tokens], dtype=torch.long)
    with torch.no_grad():
        p_prefix = model(prefix)[0, -1, kcs[t]]
        p_full = model(full)[0, t - 1, kcs[t]]
    assert abs(float(p_prefix) - float(p_full)) <= 1e-5


def _trailing_pad_is_ignored(model, tokens, n_kcs):
    model.eval()
    padded = tokens + [pad_index(n_kcs)] * 20
    x0 = torch.tensor([tokens], dtype=torch.long)
    x1 = torch.tensor([padded], dtype=torch.long)
    with torch.no_grad():
        a = model(x0)[0]
        b = model(x1)[0, : len(tokens)]
    assert torch.allclose(a, b, atol=1e-5)


def test_ut_a3_prefix_matches_masked_full_chunk():
    torch.manual_seed(2)
    n_kcs = 6
    kcs, _, tokens = _tokens(seed=2)
    _prefix_matches_full(TKTc(n_kcs, d=16, n_heads=4, n_layers=1), tokens, kcs, 5)
    from src.baseline_runner import DKT
    _prefix_matches_full(DKT(n_kcs, embed_dim=16, hidden_dim=16), tokens, kcs, 5)


def test_ut_a4_trailing_pad_does_not_change_valid_positions():
    torch.manual_seed(3)
    n_kcs = 6
    _, _, tokens = _tokens(seed=3)
    _trailing_pad_is_ignored(TKTc(n_kcs, d=16, n_heads=4, n_layers=1), tokens, n_kcs)
    from src.baseline_runner import DKT
    _trailing_pad_is_ignored(DKT(n_kcs, embed_dim=16, hidden_dim=16), tokens, n_kcs)


def test_ut_a5_target_of_position_i_is_the_next_row():
    from src.baseline_runner import KTDataset
    length = 210
    frame = pd.DataFrame({
        "user_id": [1] * length,
        "kc_id": [i % 5 for i in range(length)],
        "correct": [i % 2 for i in range(length)],
    })
    data = KTDataset(frame, {kc: kc for kc in range(5)}, max_seq_len=200).data
    assert len(data) == 2
    pairs = []
    for chunk_i, chunk in enumerate(data):
        start = chunk_i * 200
        for i, kc in enumerate(chunk["kcs"].tolist()):
            target_row = start + i + 1
            pairs.append((start + i, target_row, kc, int(frame.loc[target_row, "kc_id"])))
            assert kc == int(frame.loc[target_row, "kc_id"])
            assert kc != int(frame.loc[start + i, "kc_id"]) or int(frame.loc[start + i, "kc_id"]) == kc and target_row != start + i
    # Start, end, and the first row of the next 200-row chunk.
    checked = {pairs[0][0], pairs[198][0], pairs[199][0]}
    assert checked == {0, 198, 200}
    assert pairs[0][1] == 1 and pairs[198][1] == 199 and pairs[199][1] == 201


def test_ut_a6_short_fit_loss_is_finite_and_falls():
    torch.manual_seed(5)
    n_kcs = 4
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = nn.BCELoss()
    losses = []
    fixed = [_tokens(n_kcs=n_kcs, length=6, seed=100 + i) for i in range(64)]
    for step in range(200):
        batch = fixed[step % 64]
        xs, kcs_b, ys_b = [], [], []
        for kcs, ys, tokens in [batch]:
            xs.append(tokens[:-1])
            kcs_b.append(kcs[1:])
            ys_b.append(ys[1:])
        x = torch.tensor(xs, dtype=torch.long)
        target_kc = torch.tensor(kcs_b[0])
        target_y = torch.tensor(ys_b[0], dtype=torch.float)
        pred = model(x)[0, torch.arange(len(target_kc)), target_kc]
        loss = loss_fn(pred, target_y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    assert np.isfinite(losses).all()
    assert float(np.mean(losses[-10:])) < float(np.mean(losses[:10]))
    kcs, ys, tokens = fixed[0]
    t = 3
    flipped = tokens.copy()
    flipped[t] = 2 * kcs[t] + (1 - ys[t])
    base = chunk_model_probs(model, tokens, kcs, "cpu")
    alt = chunk_model_probs(model, flipped, kcs, "cpu")
    for row in range(1, t + 1):
        assert abs(base[row - 1] - alt[row - 1]) <= 1e-6
    _prefix_matches_full(model, tokens, kcs, 4)
    _trailing_pad_is_ignored(model, tokens, n_kcs)


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


def _states_equal(left, right) -> bool:
    return all(torch.equal(left[key], right[key]) for key in left)


def test_ut_c1_best_valid_restores_max_validation_epoch():
    """Train 5 epochs. Validation AUC is forced so epoch 1 is best and epoch 4 is last."""
    from sklearn import metrics as sk_metrics
    from torch.utils.data import DataLoader, Dataset

    from src.baseline_runner import train_torch_model

    class Tiny(nn.Module):
        def __init__(self):
            super().__init__()
            self.n_kcs = 2
            self.lin = nn.Linear(1, 2)

        def forward(self, x):
            batch, seq = x.shape
            ones = torch.ones(batch, seq, 1, device=x.device)
            return torch.sigmoid(self.lin(ones))

    class Rows(Dataset):
        def __len__(self):
            return 4

        def __getitem__(self, idx):
            feats = torch.tensor([idx % 2, 1], dtype=torch.long)
            labels = torch.tensor([float(idx % 2), 1.0])
            kcs = torch.tensor([0, 1])
            return feats, labels, kcs

    planned = [0.60, 0.95, 0.80, 0.70, 0.55]
    cursor = {"i": 0}

    def fake_auc(y_true, y_score):
        value = planned[cursor["i"]]
        cursor["i"] += 1
        return value

    original = sk_metrics.roc_auc_score
    sk_metrics.roc_auc_score = fake_auc
    try:
        loader = DataLoader(Rows(), batch_size=4)
        copies = []
        model = train_torch_model(
            Tiny(),
            loader,
            loader,
            torch.device("cpu"),
            n_epochs=5,
            lr=0.5,
            select="best_valid",
            patience=8,
            copies=copies,
        )
    finally:
        sk_metrics.roc_auc_score = original
    assert len(copies) == 5
    assert model.selected_epoch == 1
    assert _states_equal(model.state_dict(), copies[1])
    assert not _states_equal(copies[1], copies[4])


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


def test_ut_w2_full_and_slide_count_learners_and_chunk_counts_chunks():
    torch.manual_seed(8)
    n_kcs = 5
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    rows = []
    lengths = (5, 1, 4)
    for user, length in enumerate(lengths, start=1):
        for i in range(length):
            rows.append({
                "user_id": user,
                "timestamp": i,
                "kc_id": i % n_kcs,
                "correct": i % 2,
            })
    frame = pd.DataFrame(rows)
    kc_map = {i: i for i in range(n_kcs)}
    window = 3
    for mode in ("full", "slide", "chunk"):
        scored = predict_windowed(model, frame, kc_map, "cpu", window=window, mode=mode)
        observed = sum(row[4] == 1 for row in scored)
        assert observed == no_history_counts(lengths, window, mode)


def test_score_windowed_matches_predict_windowed():
    torch.manual_seed(11)
    n_kcs = 5
    model = TKTc(n_kcs, d=16, n_heads=4, n_layers=1)
    model.eval()
    rows = []
    for user, length in ((1, 1), (2, 5), (3, 7)):
        for i in range(length):
            rows.append({
                "user_id": user,
                "timestamp": i,
                "kc_id": (user + i) % n_kcs,
                "correct": (user + i) % 2,
            })
    frame = pd.DataFrame(rows)
    kc_map = {i: i for i in range(n_kcs)}
    for mode in ("full", "chunk", "slide"):
        slow = predict_windowed(model, frame, kc_map, "cpu", window=3, mode=mode)
        fast = score_windowed(model, frame, kc_map, "cpu", window=3, mode=mode, batch_size=2)
        assert len(slow) == len(fast)
        for a, b in zip(slow, fast):
            assert a[:5] == b[:5]
            if a[5] != a[5]:
                assert b[5] != b[5]
            else:
                assert abs(a[5] - b[5]) <= 1e-5


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
    drawn = dense_at_n(clusters, 50, np.random.default_rng(3))
    assert drawn is not None and len(drawn[0]) == 50
    user_sparse = clusters[:8]
    user_dense = [(c[0], c[1]) for c in clusters[:8]]
    boot = cluster_bootstrap_diff(user_sparse, user_dense, rng, n_boot=8, n_inner=4)
    assert boot["n_used"] > 0
    assert boot["n_empty_or_invalid"] == 0


def test_ece_sweep_stops_when_accuracy_decreases():
    increasing = ece_sweep(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]))
    decreasing = ece_sweep(np.array([1, 1, 0, 0]), np.array([0.1, 0.2, 0.8, 0.9]))
    assert increasing[1] >= 2
    assert decreasing[1] == 1
    perfect = kumar_squared_ce(np.array([0, 0, 1, 1, 0, 1]), np.array([0.0, 0.0, 1.0, 1.0, 0.0, 1.0]))
    assert perfect <= 1e-8


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
