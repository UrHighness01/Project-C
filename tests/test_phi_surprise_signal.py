#!/usr/bin/env python3
"""Tests for algorithms/PhiSurpriseSignal.py."""
import sys
import math
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.PhiSurpriseSignal as pss


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_entries(phi_series, base_ts=1_000_000.0, dt=60.0):
    """Build newest-first history; phi_series[0]=oldest, phi_series[-1]=newest."""
    n = len(phi_series)
    entries = [
        {"timestamp": base_ts + i * dt, "mean_phi_level": float(v)}
        for i, v in enumerate(phi_series)
    ]
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    original = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_entries(phi_series)
        return pss.analyse("albedo", **kw)
    finally:
        if original is not None:
            chs.load = original


def _ar1(n=80, alpha=0.9, noise=0.02, seed=3):
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = 1.0
    for i in range(1, n):
        x[i] = alpha * x[i - 1] + rng.normal(0, noise)
    return x


def _flat(n=60, val=1.0):
    return np.full(n, val)


def _step_change(n=60, step_at=45, low=1.0, high=2.0):
    """Series that is flat until step_at, then jumps to high."""
    x = np.full(n, low)
    x[step_at:] = high
    return x


# ── Unit: _build_ar_matrix ─────────────────────────────────────────────────────

class TestBuildArMatrix:
    def test_shape(self):
        s = np.arange(20.0)
        X, y = pss._build_ar_matrix(s, 3)
        assert X.shape == (17, 3)
        assert y.shape == (17,)


# ── Unit: _fit_ar ──────────────────────────────────────────────────────────────

class TestFitAr:
    def test_returns_vector_of_length_p(self):
        a = pss._fit_ar(np.arange(30.0), 4)
        assert a.shape == (4,)

    def test_ar1_coefficient_recovered(self):
        phi = _ar1(n=200, alpha=0.85, noise=0.005, seed=7)
        a = pss._fit_ar(phi, 1)
        assert abs(a[0] - 0.85) < 0.05


# ── Unit: _one_step_pred ───────────────────────────────────────────────────────

class TestOneStepPred:
    def test_ar1_identity_prediction(self):
        """AR(1) with alpha=1.0 should predict phi[t] = phi[t-1]."""
        phi = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        a = np.array([1.0])
        pred = pss._one_step_pred(phi, a, 4)
        assert pred == pytest.approx(4.0, abs=1e-6)

    def test_ar2_uses_two_lags(self):
        phi = np.array([0.0, 1.0, 0.0, 1.0])
        a = np.array([0.5, 0.5])
        pred = pss._one_step_pred(phi, a, 3)
        # [phi(2), phi(1)] = [0, 1]; dot([0.5,0.5],[0,1]) = 0.5
        assert pred == pytest.approx(0.5, abs=1e-6)


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_calm(self):
        assert pss._classify(0.1, 0.5, 2.0) == "CALM"

    def test_surprised(self):
        assert pss._classify(0.1, 3.0, 2.0) == "SURPRISED"

    def test_meta_surprise_wins_over_surprised(self):
        assert pss._classify(0.6, 3.0, 2.0) == "META_SURPRISE"

    def test_meta_surprise_alone(self):
        assert pss._classify(0.6, 0.5, 2.0) == "META_SURPRISE"


# ── Unit: _extract_phi ────────────────────────────────────────────────────────

class TestExtractPhi:
    def test_oldest_first(self):
        entries = _make_entries([1.0, 2.0, 3.0])
        phi = pss._extract_phi(entries)
        np.testing.assert_allclose(phi, [1.0, 2.0, 3.0], atol=1e-6)

    def test_missing_key_skipped(self):
        entries = [{"timestamp": 10.0}, {"timestamp": 0.0, "mean_phi_level": 5.0}]
        phi = pss._extract_phi(entries)
        assert list(phi) == [5.0]


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_returns_default(self):
        r = _run([1.0] * 5)
        assert r.n_eval_steps == 0
        assert r.surprise_class == "CALM"

    def test_returns_result_type(self):
        r = _run(_ar1())
        assert isinstance(r, pss.PhiSurpriseResult)

    def test_eval_steps_positive(self):
        r = _run(_ar1(n=80))
        assert r.n_eval_steps > 0

    def test_train_steps_positive(self):
        r = _run(_ar1(n=80))
        assert r.n_train_steps > 0

    def test_mean_abs_z_nonneg(self):
        r = _run(_ar1())
        assert r.mean_abs_z >= 0.0

    def test_max_abs_z_gte_mean(self):
        r = _run(_ar1())
        assert r.max_abs_z >= r.mean_abs_z - 1e-6

    def test_sigma_residual_positive(self):
        r = _run(_ar1())
        assert r.sigma_residual > 0.0

    def test_surprise_rate_in_unit_interval(self):
        r = _run(_ar1())
        assert 0.0 <= r.surprise_rate <= 1.0

    def test_surprise_class_valid(self):
        r = _run(_ar1())
        assert r.surprise_class in {"CALM", "SURPRISED", "META_SURPRISE"}

    def test_to_dict_keys(self):
        r = _run(_ar1())
        d = r.to_dict()
        for k in ("current_surprise_z", "surprise_rate", "mean_abs_z",
                  "max_abs_z", "meta_surprise_flag", "surprise_class",
                  "sigma_residual", "n_eval_steps", "n_train_steps"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_ar1())
        json.dumps(r.to_dict())

    def test_deterministic(self):
        phi = _ar1(n=80)
        r1 = _run(phi)
        r2 = _run(phi)
        assert r1.current_surprise_z == r2.current_surprise_z
        assert r1.surprise_rate == r2.surprise_rate

    def test_flat_series_calm(self):
        """Flat phi → residuals near zero → sigma too small → default CALM result."""
        r = _run(_flat(n=60))
        assert r.surprise_class == "CALM"
        # Either no eval steps (early return on flat) or z-scores are small
        assert r.mean_abs_z < 10.0

    def test_step_change_triggers_surprise(self):
        """Series flat for 60 steps then jumps: AR trained on flat is surprised at jump.
        Use AR(1) on a noisy flat series so sigma > 0 but jump magnitude >> sigma."""
        rng = np.random.default_rng(5)
        phi = np.concatenate([
            1.0 + rng.normal(0, 0.05, 60),   # noisy flat training region
            np.full(20, 4.0),                  # big jump in eval region
        ])
        r = _run(phi, train_fraction=0.75, surprise_threshold=2.0, ar_order=1)
        assert r.max_abs_z > 2.0

    def test_step_change_surprise_rate_high(self):
        rng = np.random.default_rng(6)
        phi = np.concatenate([
            1.0 + rng.normal(0, 0.05, 60),
            np.full(20, 5.0),
        ])
        r = _run(phi, train_fraction=0.75, surprise_threshold=1.5, ar_order=1)
        assert r.surprise_rate > 0.0

    def test_structured_ar1_lower_surprise_than_noise(self):
        """AR(1) should produce lower surprise than pure white noise with same amplitude."""
        rng = np.random.default_rng(99)
        phi_ar = _ar1(n=80, alpha=0.9, noise=0.05, seed=12)
        phi_noise = rng.standard_normal(80) + 1.0
        r_ar    = _run(phi_ar,    ar_order=1, train_fraction=0.75)
        r_noise = _run(phi_noise, ar_order=1, train_fraction=0.75)
        # AR(1) model should fit its own data better → lower mean |z|
        assert r_ar.mean_abs_z <= r_noise.mean_abs_z + 0.5

    def test_meta_surprise_flag_true_when_rate_high(self):
        """Force high surprise rate by using a very small threshold."""
        r = _run(_ar1(n=80), surprise_threshold=0.001)
        assert r.meta_surprise_flag is True
        assert r.surprise_class == "META_SURPRISE"

    def test_meta_surprise_flag_false_for_smooth(self):
        r = _run(_flat(n=60))
        assert r.meta_surprise_flag is False

    def test_n_train_n_eval_partition(self):
        phi = _ar1(n=80)
        r = _run(phi, train_fraction=0.75)
        # train + eval = total - p (approx, due to AR lags), at least consistent
        assert r.n_train_steps + r.n_eval_steps <= 80
        assert r.n_eval_steps > 0
