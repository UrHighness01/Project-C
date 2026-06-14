#!/usr/bin/env python3
"""Tests for algorithms/CognitiveLoadEstimator.py."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.CognitiveLoadEstimator as cle


def _analyse(active=None, total=None, phi=2.0, qc=200):
    a = active if active is not None else [0.5, 0.7]
    t = total if total is not None else [0.5, 0.7, 0.8, 0.9]
    return cle.analyse(a, t, phi, qc)


class TestClassify:
    def test_idle(self):
        assert cle._classify(0.1) == "IDLE"

    def test_low(self):
        assert cle._classify(0.35) == "LOW"

    def test_moderate(self):
        assert cle._classify(0.6) == "MODERATE"

    def test_high(self):
        assert cle._classify(0.8) == "HIGH"

    def test_overloaded(self):
        assert cle._classify(0.95) == "OVERLOADED"


class TestAnalyse:
    def test_returns_result(self):
        result = _analyse()
        assert isinstance(result, cle.CognitiveLoadResult)

    def test_load_in_range(self):
        result = _analyse()
        assert 0.0 <= result.load_index <= 1.0

    def test_all_active_high_aar(self):
        p = [0.8, 0.9, 0.7]
        result = cle.analyse(p, p, phi=2.0, qualia_count=100)
        assert result.algorithm_activation == pytest.approx(1.0, abs=1e-6)

    def test_none_active_zero_aar(self):
        result = cle.analyse([], [0.5, 0.8, 0.9], phi=2.0, qualia_count=100)
        assert result.algorithm_activation == pytest.approx(0.0, abs=1e-6)

    def test_no_algorithms_zero_aar(self):
        result = cle.analyse([], [], phi=2.0, qualia_count=100)
        assert result.algorithm_activation == 0.0

    def test_active_algorithms_count(self):
        result = cle.analyse([0.5, 0.7, 0.8], [0.5, 0.7, 0.8, 0.9], 2.0, 100)
        assert result.active_algorithms == 3

    def test_total_algorithms_count(self):
        result = cle.analyse([0.5], [0.5, 0.7, 0.8, 0.9], 2.0, 100)
        assert result.total_algorithms == 4

    def test_valid_load_class(self):
        result = _analyse()
        assert result.load_class in {"IDLE", "LOW", "MODERATE", "HIGH", "OVERLOADED"}

    def test_high_qualia_low_phi_raises_pdr(self):
        # Many qualia, tiny phi → high PDR
        result = cle.analyse([0.5], [0.5], phi=0.001, qualia_count=50000, pdr_ref=5000.0)
        assert result.qualia_density_ratio > 0.5

    def test_low_qualia_high_phi_low_pdr(self):
        result = cle.analyse([0.5], [0.5], phi=10.0, qualia_count=10, pdr_ref=5000.0)
        assert result.qualia_density_ratio < 0.1

    def test_phi_stored(self):
        result = cle.analyse([0.5], [0.5], phi=3.14, qualia_count=100)
        assert result.phi == pytest.approx(3.14, abs=1e-4)

    def test_qualia_count_stored(self):
        result = cle.analyse([0.5], [0.5], phi=2.0, qualia_count=999)
        assert result.qualia_count == 999

    def test_load_clipped_to_one(self):
        result = cle.analyse([1.0] * 10, [1.0] * 10, phi=0.0001, qualia_count=999999)
        assert result.load_index <= 1.0

    def test_load_clipped_to_zero(self):
        result = cle.analyse([], [0.5], phi=100.0, qualia_count=0)
        assert result.load_index >= 0.0

    def test_alpha_zero_uses_only_pdr(self):
        result = cle.analyse([0.5], [0.5], phi=2.0, qualia_count=100, alpha=0.0)
        assert result.load_index == pytest.approx(result.qualia_density_ratio, rel=1e-5)

    def test_alpha_one_uses_only_aar(self):
        result = cle.analyse([0.5], [1.0], phi=2.0, qualia_count=100, alpha=1.0)
        assert result.load_index == pytest.approx(result.algorithm_activation, rel=1e-5)

    def test_to_dict_serialisable(self):
        import json
        json.dumps(_analyse().to_dict())

    def test_to_dict_keys(self):
        d = _analyse().to_dict()
        for k in ("load_index", "load_class", "algorithm_activation",
                  "qualia_density_ratio", "active_algorithms",
                  "total_algorithms", "phi", "qualia_count"):
            assert k in d

    def test_overloaded_all_active_high_qualia(self):
        p = [1.0] * 10
        result = cle.analyse(p, p, phi=0.0001, qualia_count=100000, pdr_ref=100.0)
        assert result.load_class in {"HIGH", "OVERLOADED"}
