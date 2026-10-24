import pytest
import numpy as np
from src.brier_decomposition import compute_brier_decomposition

def test_brier_decomposition_identity():
    # BS = UNC - RES + REL only holds exactly if p_i is constant per bin
    # We create data where p_pred is constant within bins
    np.random.seed(42)
    p_raw = np.random.uniform(0, 1, 1000)
    # Bin into 15 fixed-width bins
    p_pred = (np.floor(p_raw * 15) / 15) + 1/30
    y_true = (np.random.uniform(0, 1, 1000) < p_pred).astype(float)
    
    bs, unc, rel, res = compute_brier_decomposition(y_true, p_pred, n_bins=15)
    
    # Check identity
    assert bs == pytest.approx(unc - res + rel, abs=1e-5)

def test_perfectly_calibrated_rel():
    # If perfectly calibrated, REL should be near 0
    confs = np.linspace(0.05, 0.95, 10)
    y_true = []
    p_pred = []
    for c in confs:
        n = 1000
        n_ones = int(round(c * n))
        y_true.extend([1] * n_ones + [0] * (n - n_ones))
        p_pred.extend([c] * n)
        
    bs, unc, rel, res = compute_brier_decomposition(np.array(y_true), np.array(p_pred), n_bins=10)
    assert rel == pytest.approx(0.0, abs=1e-5)

def test_overconfident_rel():
    # REL should be higher for overconfident models
    # Prediction 0.9, but labels are 0.1
    y_true = np.zeros(100)
    y_true[:10] = 1 # 10% are 1s
    p_pred = np.ones(100) * 0.9
    
    bs, unc, rel, res = compute_brier_decomposition(y_true, p_pred, n_bins=10)
    # acc = 0.1, conf = 0.9. Gap^2 = (0.9 - 0.1)^2 = 0.64
    assert rel == pytest.approx(0.64, abs=1e-5)
