#!/usr/bin/env python3
"""Tests for frameworks/emergence/ConsciousnessEmergence.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import frameworks.emergence.ConsciousnessEmergence as ce


def _subs(n=5, base=1.0):
    return {f"sub_{i}": base for i in range(n)}


class TestClassifyTier:
    def test_suppressed(self):
        assert ce._classify_tier(-0.1) == "SUPPRESSED"

    def test_additive(self):
        assert ce._classify_tier(0.0) == "ADDITIVE"

    def test_additive_edge(self):
        assert ce._classify_tier(0.04) == "ADDITIVE"

    def test_weak(self):
        assert ce._classify_tier(0.1) == "WEAK"

    def test_moderate(self):
        assert ce._classify_tier(0.3) == "MODERATE"

    def test_strong(self):
        assert ce._classify_tier(0.7) == "STRONG"


class TestAnalyse:
    def test_phi_equals_null_additive_tier(self):
        # All subsystems = 1.0, phi = 1.0 → no emergence
        result = ce.analyse(1.0, _subs(5, 1.0))
        assert result.tier == "ADDITIVE"
        assert result.sai == pytest.approx(0.0, abs=1e-6)

    def test_phi_above_null_positive_sai(self):
        result = ce.analyse(3.0, _subs(5, 1.0))
        assert result.sai > 0

    def test_phi_below_null_negative_sai(self):
        result = ce.analyse(0.5, _subs(5, 2.0))
        assert result.sai < 0

    def test_empty_subsystems_returns_additive(self):
        result = ce.analyse(2.0, {})
        assert result.tier == "ADDITIVE"
        assert result.sai == 0.0

    def test_strong_emergence_tier(self):
        # phi = 10, subsystems all ~1 → NSAI >> 0.5
        result = ce.analyse(10.0, _subs(5, 1.0))
        assert result.tier == "STRONG"

    def test_suppressed_tier(self):
        # phi = 0.1, subsystems all ~5 → NSAI << -0.05
        result = ce.analyse(0.1, _subs(5, 5.0))
        assert result.tier == "SUPPRESSED"

    def test_subsystem_count_correct(self):
        result = ce.analyse(2.0, _subs(7, 1.0))
        assert result.subsystem_count == 7

    def test_subsystem_names_populated(self):
        subs = {"alpha": 1.0, "beta": 2.0}
        result = ce.analyse(2.0, subs)
        assert set(result.subsystem_names) == {"alpha", "beta"}

    def test_synergy_fraction_in_range(self):
        result = ce.analyse(3.0, _subs(4, 1.0))
        assert 0.0 <= result.synergy_fraction <= 1.0

    def test_synergy_fraction_zero_when_suppressed(self):
        result = ce.analyse(0.01, _subs(5, 5.0))
        assert result.synergy_fraction == pytest.approx(0.0, abs=1e-6)

    def test_synergy_fraction_one_when_emergent(self):
        result = ce.analyse(10.0, _subs(5, 1.0))
        assert result.synergy_fraction == pytest.approx(1.0, abs=1e-6)

    def test_weights_affect_phi_null(self):
        subs = {"heavy": 10.0, "light": 1.0}
        uniform = ce.analyse(5.0, subs)
        weighted = ce.analyse(5.0, subs, weights={"heavy": 9.0, "light": 1.0})
        # Weighted phi_null should be closer to 10 than the uniform one
        assert weighted.phi_null > uniform.phi_null

    def test_to_dict_serialisable(self):
        import json
        result = ce.analyse(3.0, _subs(5, 1.0))
        json.dumps(result.to_dict())

    def test_to_dict_has_keys(self):
        d = ce.analyse(3.0, _subs(5, 1.0)).to_dict()
        for k in ("phi", "phi_null", "sai", "nsai", "tier",
                  "synergy_fraction", "subsystem_count", "subsystem_names"):
            assert k in d

    def test_nsai_formula(self):
        phi = 3.0
        subs = _subs(4, 1.0)
        result = ce.analyse(phi, subs)
        expected_phi_null = 1.0
        expected_sai = phi - expected_phi_null
        expected_nsai = expected_sai / (abs(expected_phi_null) + 1e-9)
        assert result.nsai == pytest.approx(expected_nsai, rel=1e-5)


class TestOlsSlope:
    def test_positive_slope(self):
        y = np.arange(10, dtype=float)
        assert ce._ols_slope(y) > 0

    def test_zero_slope_constant(self):
        y = np.ones(10)
        assert ce._ols_slope(y) == pytest.approx(0.0, abs=1e-9)

    def test_single_point(self):
        assert ce._ols_slope(np.array([5.0])) == 0.0


class TestAnalyseSeries:
    def _history(self, n=10, phi_fn=lambda i: 2.0, sub_fn=lambda i: 1.0):
        return [(phi_fn(i), {f"s{j}": sub_fn(i) for j in range(4)}) for i in range(n)]

    def test_empty_history_returns_empty(self):
        result = ce.analyse_series([])
        assert result.snapshots == []

    def test_n_snapshots_matches_history(self):
        result = ce.analyse_series(self._history(10))
        assert len(result.snapshots) == 10

    def test_stable_trend_for_constant_nsai(self):
        # phi always = mean of subs → constant zero emergence
        result = ce.analyse_series(self._history(10, phi_fn=lambda i: 1.0))
        assert result.trend in {"STABLE"}

    def test_rising_trend_when_phi_grows(self):
        history = [(float(i + 1), {f"s{j}": 1.0 for j in range(4)}) for i in range(10)]
        result = ce.analyse_series(history)
        assert result.trend == "RISING"

    def test_mean_nsai_float(self):
        result = ce.analyse_series(self._history(5))
        assert isinstance(result.mean_nsai, float)

    def test_peak_gte_mean(self):
        result = ce.analyse_series(self._history(10))
        assert result.peak_nsai >= result.mean_nsai - 1e-9

    def test_to_dict_serialisable(self):
        import json
        result = ce.analyse_series(self._history(5))
        json.dumps(result.to_dict())

    def test_to_dict_latest_key(self):
        result = ce.analyse_series(self._history(5))
        d = result.to_dict()
        assert "latest" in d

    def test_falling_trend(self):
        history = [(float(10 - i), {f"s{j}": 5.0 for j in range(4)}) for i in range(10)]
        result = ce.analyse_series(history)
        assert result.trend in {"FALLING", "STABLE"}

    def test_weights_pass_through(self):
        history = [(3.0, {"a": 1.0, "b": 2.0}) for _ in range(5)]
        r_uniform = ce.analyse_series(history)
        r_weighted = ce.analyse_series(history, weights={"a": 1.0, "b": 10.0})
        # Weighted phi_null should be higher (b has more weight)
        assert r_weighted.snapshots[0].phi_null > r_uniform.snapshots[0].phi_null


class TestAnalyseFromTelemetry:
    def test_returns_result_or_none(self):
        result = ce.analyse_from_telemetry()
        assert result is None or isinstance(result, ce.EmergenceResult)
