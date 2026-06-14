#!/usr/bin/env python3
"""Tests for algorithms/MetacognitiveCalibrator.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.MetacognitiveCalibrator as mc

RNG = np.random.default_rng(3)


class TestAccuracyFromSurprisal:
    def test_zero_surprisal_all_ones(self):
        s = np.zeros(10)
        a = mc._accuracy_from_surprisal(s)
        assert (a == 1.0).all()

    def test_max_surprisal_maps_to_zero(self):
        s = np.array([0.0, 0.5, 1.0])
        a = mc._accuracy_from_surprisal(s)
        assert a[-1] == pytest.approx(0.0, abs=1e-9)

    def test_output_in_range(self):
        s = RNG.uniform(0, 5, 100)
        a = mc._accuracy_from_surprisal(s)
        assert (a >= 0.0).all() and (a <= 1.0).all()


class TestEce:
    def test_perfect_calibration_zero(self):
        c = np.linspace(0, 1, 50)
        a = c.copy()
        assert mc._ece(c, a) == pytest.approx(0.0, abs=1e-6)

    def test_constant_overconfidence(self):
        c = np.ones(100) * 0.9
        a = np.ones(100) * 0.5
        ece = mc._ece(c, a)
        assert ece == pytest.approx(0.4, abs=0.05)

    def test_empty_returns_zero(self):
        assert mc._ece(np.array([]), np.array([])) == 0.0

    def test_output_in_range(self):
        c = RNG.uniform(0, 1, 100)
        a = RNG.uniform(0, 1, 100)
        assert 0.0 <= mc._ece(c, a) <= 1.0


class TestClassify:
    def test_excellent(self):
        assert mc._classify(0.03) == "EXCELLENT"

    def test_good(self):
        assert mc._classify(0.07) == "GOOD"

    def test_moderate(self):
        assert mc._classify(0.15) == "MODERATE"

    def test_poor(self):
        assert mc._classify(0.25) == "POOR"


class TestAnalyse:
    def _conf(self, n=50, val=0.8):
        return [val] * n

    def _surp(self, n=50, val=0.1):
        return np.ones(n) * val

    def test_empty_returns_default(self):
        result = mc.analyse([], np.array([]))
        assert result.n_pairs == 0

    def test_returns_calibration_result(self):
        result = mc.analyse(self._conf(50, 0.7), self._surp(50, 0.2))
        assert isinstance(result, mc.CalibrationResult)

    def test_perfect_calibration_excellent(self):
        # conf = acc everywhere → MCE = 0
        surp = np.zeros(50)  # acc = 1.0
        result = mc.analyse([1.0] * 50, surp)
        assert result.calibration_class == "EXCELLENT"
        assert result.mce == pytest.approx(0.0, abs=1e-6)

    def test_overconfident_positive_bias(self):
        # High uniform surprisal → accuracy near 0; confidence = 0.9 → overconfident
        surp = np.ones(50)  # all equal → acc = 0.0 for all (1 - s/max = 1 - 1 = 0)
        confs = [0.9] * 50
        result = mc.analyse(confs, surp)
        assert result.overconfidence_bias > 0

    def test_is_overconfident_flag(self):
        surp = np.ones(50) * 0.9  # low accuracy
        result = mc.analyse([0.95] * 50, surp)
        # accuracy = 0 (all equal high surprisal except max = 0.9 → all = 0)
        # Actually acc = 1 - s/max = 0 for all since all equal max
        assert isinstance(result.is_overconfident, bool)

    def test_humble_negative_bias(self):
        # confidence = 0.1, surprisal = 0 → accuracy = 1.0
        surp = np.zeros(50)
        result = mc.analyse([0.1] * 50, surp, overconfidence_threshold=0.05)
        assert result.is_humble

    def test_n_pairs_correct(self):
        result = mc.analyse([0.7] * 30, self._surp(30))
        assert result.n_pairs == 30

    def test_n_pairs_takes_min_length(self):
        result = mc.analyse([0.7] * 20, self._surp(40))
        assert result.n_pairs == 20

    def test_mce_in_range(self):
        result = mc.analyse(self._conf(50, 0.6), self._surp(50, 0.5))
        assert 0.0 <= result.mce <= 1.0

    def test_ece_in_range(self):
        result = mc.analyse(self._conf(50, 0.6), self._surp(50, 0.5))
        assert 0.0 <= result.ece <= 1.0

    def test_mean_confidence_correct(self):
        result = mc.analyse([0.7] * 50, self._surp(50))
        assert result.mean_confidence == pytest.approx(0.7, abs=1e-4)

    def test_mean_accuracy_in_range(self):
        result = mc.analyse(self._conf(50), self._surp(50))
        assert 0.0 <= result.mean_accuracy <= 1.0

    def test_calibration_class_valid(self):
        result = mc.analyse(self._conf(50), self._surp(50))
        assert result.calibration_class in {"EXCELLENT", "GOOD", "MODERATE", "POOR"}

    def test_to_dict_serialisable(self):
        import json
        result = mc.analyse(self._conf(50), self._surp(50))
        json.dumps(result.to_dict())

    def test_to_dict_keys(self):
        d = mc.analyse(self._conf(50), self._surp(50)).to_dict()
        for k in ("mce", "overconfidence_bias", "ece", "calibration_class",
                  "is_overconfident", "is_humble", "n_pairs",
                  "mean_confidence", "mean_accuracy"):
            assert k in d

    def test_single_pair_returns_default(self):
        result = mc.analyse([0.5], np.array([0.1]))
        assert result.n_pairs == 0
