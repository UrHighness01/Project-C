#!/usr/bin/env python3
"""Tests for algorithms/PhenomenalUnityIndex.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.PhenomenalUnityIndex as pui


def _snap(phi=1.0, qualia_count=100, valence=0.5, arousal=0.5,
          confidence=0.8, mean_novelty=0.3, combined_continuity=0.7):
    return {"summary": {
        "phi": phi, "qualia_count": qualia_count, "valence": valence,
        "arousal": arousal, "confidence": confidence,
        "mean_novelty": mean_novelty, "combined_continuity": combined_continuity,
    }}


def _correlated_snaps(n=20):
    """All dimensions move together — should produce high unity."""
    rng = np.random.default_rng(1)
    base = rng.normal(0, 1, n)
    snaps = []
    for i in range(n):
        v = float(base[i])
        snaps.append(_snap(
            phi=1.0 + 0.5 * v,
            qualia_count=int(100 + 20 * v),
            valence=0.5 + 0.1 * v,
            arousal=0.5 + 0.1 * v,
            confidence=0.7 + 0.05 * v,
            mean_novelty=0.3 + 0.05 * v,
            combined_continuity=0.6 + 0.05 * v,
        ))
    return snaps


def _independent_snaps(n=20):
    """All dimensions evolve independently — low unity."""
    rng = np.random.default_rng(42)
    snaps = []
    for _ in range(n):
        snaps.append(_snap(
            phi=float(rng.uniform(0.5, 3.0)),
            qualia_count=int(rng.uniform(50, 300)),
            valence=float(rng.uniform(-1, 1)),
            arousal=float(rng.uniform(0, 1)),
            confidence=float(rng.uniform(0.3, 1.0)),
            mean_novelty=float(rng.uniform(0, 1)),
            combined_continuity=float(rng.uniform(0, 1)),
        ))
    return snaps


class TestExtractSeries:
    def test_returns_matrix_and_names(self):
        snaps = _correlated_snaps(10)
        X, dims = pui._extract_series(snaps)
        assert X.ndim == 2
        assert len(dims) > 0

    def test_empty_snaps_empty_output(self):
        X, dims = pui._extract_series([])
        assert X.size == 0

    def test_no_nans_in_output(self):
        snaps = _correlated_snaps(10)
        X, _ = pui._extract_series(snaps)
        assert not np.isnan(X).any()

    def test_row_count_matches_snapshots(self):
        snaps = _correlated_snaps(15)
        X, _ = pui._extract_series(snaps)
        assert X.shape[0] == 15


class TestClassify:
    def test_unified(self):
        assert pui._classify(0.6) == "UNIFIED"

    def test_partial(self):
        assert pui._classify(0.35) == "PARTIAL"

    def test_fragmented(self):
        assert pui._classify(0.1) == "FRAGMENTED"


class TestAnalyse:
    def test_empty_returns_default(self):
        result = pui.analyse([])
        assert result.unity_index == 0.0

    def test_too_few_timepoints_returns_default(self):
        result = pui.analyse([_snap()] * 2)
        assert isinstance(result, pui.PhenomenalUnityResult)

    def test_returns_result_type(self):
        result = pui.analyse(_correlated_snaps(20))
        assert isinstance(result, pui.PhenomenalUnityResult)

    def test_unity_in_range(self):
        result = pui.analyse(_correlated_snaps(20))
        assert 0.0 <= result.unity_index <= 1.0

    def test_pc1_in_range(self):
        result = pui.analyse(_correlated_snaps(20))
        assert 0.0 <= result.pc1_fraction <= 1.0

    def test_correlated_snaps_high_unity(self):
        result = pui.analyse(_correlated_snaps(30))
        assert result.unity_index > 0.5
        assert result.unity_class == "UNIFIED"

    def test_independent_snaps_lower_unity(self):
        corr = pui.analyse(_correlated_snaps(30))
        indep = pui.analyse(_independent_snaps(30))
        assert corr.unity_index > indep.unity_index

    def test_correlated_high_pc1(self):
        result = pui.analyse(_correlated_snaps(30))
        assert result.pc1_fraction > 0.5

    def test_n_dimensions_positive(self):
        result = pui.analyse(_correlated_snaps(20))
        assert result.n_dimensions >= 2

    def test_dimension_names_populated(self):
        result = pui.analyse(_correlated_snaps(20))
        assert len(result.dimension_names) > 0

    def test_n_timepoints_correct(self):
        result = pui.analyse(_correlated_snaps(20))
        assert result.n_timepoints == 20

    def test_correlation_matrix_shape(self):
        result = pui.analyse(_correlated_snaps(20))
        k = result.n_dimensions
        assert len(result.correlation_matrix) == k
        assert all(len(row) == k for row in result.correlation_matrix)

    def test_correlation_matrix_diagonal_one(self):
        result = pui.analyse(_correlated_snaps(20))
        for i, row in enumerate(result.correlation_matrix):
            assert row[i] == pytest.approx(1.0, abs=1e-4)

    def test_unity_class_valid(self):
        result = pui.analyse(_correlated_snaps(20))
        assert result.unity_class in {"UNIFIED", "PARTIAL", "FRAGMENTED"}

    def test_to_dict_serialisable(self):
        import json
        result = pui.analyse(_correlated_snaps(20))
        json.dumps(result.to_dict())

    def test_to_dict_keys(self):
        d = pui.analyse(_correlated_snaps(20)).to_dict()
        for k in ("unity_index", "pc1_fraction", "unity_class", "n_dimensions",
                  "dimension_names", "n_timepoints", "correlation_matrix"):
            assert k in d

    def test_constant_dimension_handled(self):
        # One dimension is constant — std=0, should not crash
        snaps = [_snap(phi=2.0) for _ in range(20)]
        result = pui.analyse(snaps)
        assert isinstance(result, pui.PhenomenalUnityResult)

    def test_null_baseline_independent_lower(self):
        # Independent snaps should have clearly lower unity than correlated
        rng = np.random.default_rng(77)
        indep = [_snap(
            phi=float(rng.uniform(0.5, 3.0)),
            valence=float(rng.uniform(-1, 1)),
            arousal=float(rng.uniform(0, 1)),
        ) for _ in range(30)]
        r_indep = pui.analyse(indep)
        r_corr = pui.analyse(_correlated_snaps(30))
        assert r_corr.unity_index > r_indep.unity_index
