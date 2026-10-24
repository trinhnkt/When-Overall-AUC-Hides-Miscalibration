import pytest
import numpy as np
from src.calibration_eval import compute_ece

def test_ece_perfect_calibration():
    # Bin size 10, each bin has confidence matching accuracy
    n_bins = 10
    confs = np.linspace(0.05, 0.95, n_bins)
    
    y_true = []
    p_pred = []
    for c in confs:
        # Use more samples and exact rounding to avoid float noise
        n_samples = 1000
        n_ones = int(round(c * n_samples))
        y_true.extend([1] * n_ones + [0] * (n_samples - n_ones))
        p_pred.extend([c] * n_samples)
        
    y_true = np.array(y_true)
    p_pred = np.array(p_pred)
    
    ece, counts, confs_out, accs_out, gaps_out = compute_ece(y_true, p_pred, n_bins=n_bins)
    
    assert ece == pytest.approx(0.0, abs=1e-5)
    for gap in gaps_out:
        if not np.isnan(gap):
            assert gap == pytest.approx(0.0, abs=1e-5)

def test_ece_overconfident():
    # Predictions are all 0.9, but labels are all 0
    y_true = np.zeros(100)
    p_pred = np.ones(100) * 0.9
    
    ece, counts, confs_out, accs_out, gaps_out = compute_ece(y_true, p_pred, n_bins=10)
    
    # Accuracy is 0, Confidence is 0.9. Gap is 0.9.
    # ECE = 1.0 * 0.9 = 0.9
    assert ece == pytest.approx(0.9, abs=1e-5)

def test_ece_underconfident():
    # Predictions are all 0.1, but labels are all 1
    y_true = np.ones(100)
    p_pred = np.ones(100) * 0.1
    
    ece, counts, confs_out, accs_out, gaps_out = compute_ece(y_true, p_pred, n_bins=10)
    
    # Accuracy is 1, Confidence is 0.1. Gap is 0.9.
    # ECE = 1.0 * 0.9 = 0.9
    assert ece == pytest.approx(0.9, abs=1e-5)

def test_ece_empty_input():
    y_true = np.array([])
    p_pred = np.array([])
    ece, counts, confs, accs, gaps = compute_ece(y_true, p_pred, n_bins=15)
    assert np.isnan(ece)
    assert len(counts) == 15
    assert all(np.isnan(confs))
