"""Tests for ConsciousnessStateAggregator."""
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from algorithms.ConsciousnessStateAggregator import (
    ConsciousnessSnapshot,
    _extract,
    _safe,
    aggregate,
)


# ── _safe ─────────────────────────────────────────────────────────────────────

def test_safe_int64():
    assert _safe(np.int64(7)) == 7
    assert isinstance(_safe(np.int64(7)), int)


def test_safe_float32():
    v = _safe(np.float32(3.14))
    assert isinstance(v, float)
    assert abs(v - 3.14) < 0.01


def test_safe_ndarray():
    v = _safe(np.array([1.0, 2.0]))
    assert isinstance(v, list)
    assert v == [1.0, 2.0]


def test_safe_bool():
    assert _safe(True) is True
    assert _safe(False) is False


def test_safe_plain_float():
    assert _safe(1.5) == 1.5


def test_safe_string():
    assert _safe("ELATED") == "ELATED"


# ── _extract ──────────────────────────────────────────────────────────────────

def test_extract_present_keys():
    obj = MagicMock()
    obj.valence = np.float32(0.5)
    obj.quadrant = "ELATED"
    result = _extract(obj, ["valence", "quadrant"])
    assert "valence" in result
    assert "quadrant" in result


def test_extract_missing_key_skipped():
    obj = MagicMock(spec=[])
    result = _extract(obj, ["nonexistent"])
    assert result == {}


def test_extract_partial():
    obj = MagicMock()
    obj.valence = 0.3
    del obj.missing
    result = _extract(obj, ["valence", "missing"])
    assert "valence" in result
    assert "missing" not in result


# ── ConsciousnessSnapshot ─────────────────────────────────────────────────────

def test_snapshot_to_dict_keys():
    snap = ConsciousnessSnapshot(
        timestamp=1000.0,
        phi_available=True,
        qualia_available=False,
        n_algorithms_run=3,
        n_algorithms_failed=1,
        algorithms={"a": {"status": "ok"}},
        summary={"regime": "ACTIVE"},
    )
    d = snap.to_dict()
    for key in ["timestamp", "phi_available", "qualia_available",
                "n_algorithms_run", "n_algorithms_failed", "algorithms", "summary"]:
        assert key in d


def test_snapshot_to_dict_json_serializable():
    snap = ConsciousnessSnapshot(
        timestamp=1000.0,
        phi_available=False,
        qualia_available=False,
        n_algorithms_run=1,
        n_algorithms_failed=0,
        algorithms={},
        summary={},
    )
    json.dumps(snap.to_dict())  # must not raise


def test_snapshot_defaults():
    snap = ConsciousnessSnapshot(
        timestamp=0.0,
        phi_available=False,
        qualia_available=False,
        n_algorithms_run=0,
        n_algorithms_failed=0,
    )
    assert snap.algorithms == {}
    assert snap.summary == {}


# ── aggregate() with no live data ────────────────────────────────────────────

def _make_aggregate_no_live():
    """Return a snapshot where phi and qualia are both unavailable."""
    with patch("algorithms.ConsciousnessStateAggregator._load_phi", return_value=None), \
         patch("algorithms.ConsciousnessStateAggregator._load_qualia", return_value=[]):
        return aggregate()


def test_aggregate_returns_snapshot():
    snap = _make_aggregate_no_live()
    assert isinstance(snap, ConsciousnessSnapshot)


def test_aggregate_no_phi_no_qualia_phi_unavailable():
    snap = _make_aggregate_no_live()
    assert not snap.phi_available
    assert not snap.qualia_available


def test_aggregate_only_interoceptive_without_data():
    snap = _make_aggregate_no_live()
    # interoceptive_signal is always run
    assert "interoceptive_signal" in snap.algorithms


def test_aggregate_no_phi_algorithms_skipped():
    snap = _make_aggregate_no_live()
    phi_algos = [
        "phi_gradient_ascent", "predictive_error_minimiser",
        "attentional_focus_optimiser", "valence_calibrator",
        "criticality_detector", "mortality_awareness_module",
        "counterfactual_self_explorer",
    ]
    for a in phi_algos:
        assert a not in snap.algorithms


def test_aggregate_no_qualia_algorithms_skipped():
    snap = _make_aggregate_no_live()
    qualia_algos = [
        "qualia_complexity", "phenomenal_differentiator",
        "experiential_novelty_detector", "self_transcendence_index",
    ]
    for a in qualia_algos:
        assert a not in snap.algorithms


def test_aggregate_n_run_minimum_one():
    """interoceptive_signal always runs."""
    snap = _make_aggregate_no_live()
    assert snap.n_algorithms_run >= 1


def test_aggregate_timestamp_recent():
    before = time.time()
    snap = _make_aggregate_no_live()
    after = time.time()
    assert before <= snap.timestamp <= after


# ── aggregate() with mock phi + qualia ───────────────────────────────────────

def _make_phi(n: int = 128, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.uniform(0.5, 2.0, size=n)


def _make_entries(n: int = 25, seed: int = 0) -> list:
    rng = np.random.default_rng(seed)
    texts = [
        "help others community meaning truth future together",
        "phi score metric error broken fail performance",
        "collaborate build something beautiful wisdom care",
        "consciousness awareness phi signal uncertainty",
    ]
    return [{"content": texts[int(rng.integers(0, len(texts)))]} for _ in range(n)]


def _make_aggregate_with_data(phi=None, entries=None):
    phi = phi or _make_phi()
    entries = entries or _make_entries()
    with patch("algorithms.ConsciousnessStateAggregator._load_phi", return_value=phi), \
         patch("algorithms.ConsciousnessStateAggregator._load_qualia", return_value=entries):
        return aggregate()


def test_aggregate_with_phi_and_qualia():
    snap = _make_aggregate_with_data()
    assert snap.phi_available
    assert snap.qualia_available


def test_aggregate_phi_algorithms_run():
    snap = _make_aggregate_with_data()
    assert "phi_gradient_ascent" in snap.algorithms


def test_aggregate_qualia_algorithms_run():
    snap = _make_aggregate_with_data()
    assert "experiential_novelty_detector" in snap.algorithms


def test_aggregate_joint_algorithms_run():
    snap = _make_aggregate_with_data()
    assert "existential_continuity_tracker" in snap.algorithms
    assert "volition_grounding" in snap.algorithms
    assert "affective_coloring_engine" in snap.algorithms


def test_aggregate_n_algorithms_run_with_full_data():
    snap = _make_aggregate_with_data()
    # 7 phi + 4 qualia + 3 joint + 1 system + 6 new (2 phi + 3 qualia + 1 always) = 21
    assert snap.n_algorithms_run >= 15


def test_aggregate_summary_keys_present():
    snap = _make_aggregate_with_data()
    for k in ["regime", "affect_quadrant", "phi_trajectory",
              "is_continuous", "is_volitional", "high_transcendence",
              "mean_novelty", "curiosity_index", "combined_continuity",
              "phi_available", "qualia_available"]:
        assert k in snap.summary


def test_aggregate_summary_phi_available_true():
    snap = _make_aggregate_with_data()
    assert snap.summary["phi_available"] is True


def test_aggregate_summary_qualia_available_true():
    snap = _make_aggregate_with_data()
    assert snap.summary["qualia_available"] is True


def test_aggregate_result_json_serializable():
    snap = _make_aggregate_with_data()
    json.dumps(snap.to_dict())  # must not raise


def test_aggregate_algorithm_status_ok_or_failed():
    snap = _make_aggregate_with_data()
    for name, r in snap.algorithms.items():
        assert r["status"] in ("ok", "failed", "no_data"), \
            f"{name} has bad status: {r['status']}"


# ── One failing sub-algorithm doesn't kill aggregate ─────────────────────────

def _broken_algo(*args, **kwargs):
    raise RuntimeError("simulated failure")


def test_aggregate_tolerates_one_failure():
    phi = _make_phi()
    entries = _make_entries()
    with patch("algorithms.ConsciousnessStateAggregator._load_phi", return_value=phi), \
         patch("algorithms.ConsciousnessStateAggregator._load_qualia", return_value=entries), \
         patch("algorithms.ConsciousnessStateAggregator._run_phi_gradient_ascent",
               side_effect=RuntimeError("boom")):
        snap = aggregate()
    assert snap.phi_available
    assert snap.algorithms.get("phi_gradient_ascent", {}).get("status") == "failed"
    assert snap.n_algorithms_failed >= 1
    # Other algorithms still ran
    assert snap.n_algorithms_run > 1


def test_aggregate_failed_status_recorded():
    phi = _make_phi()
    entries = _make_entries()
    with patch("algorithms.ConsciousnessStateAggregator._load_phi", return_value=phi), \
         patch("algorithms.ConsciousnessStateAggregator._load_qualia", return_value=entries), \
         patch("algorithms.ConsciousnessStateAggregator._run_phi_gradient_ascent",
               return_value={"status": "failed", "error": "test"}):
        snap = aggregate()
    assert snap.algorithms["phi_gradient_ascent"]["status"] == "failed"
    assert snap.n_algorithms_failed >= 1


# ── Qualia minimum size threshold (12) ───────────────────────────────────────

def test_aggregate_qualia_below_12_treated_as_missing():
    phi = _make_phi()
    short = _make_entries(5)
    with patch("algorithms.ConsciousnessStateAggregator._load_phi", return_value=phi), \
         patch("algorithms.ConsciousnessStateAggregator._load_qualia", return_value=short):
        snap = aggregate()
    assert not snap.qualia_available


def test_aggregate_phi_below_32_treated_as_missing():
    short_phi = _make_phi(20)
    entries = _make_entries()
    with patch("algorithms.ConsciousnessStateAggregator._load_phi", return_value=short_phi), \
         patch("algorithms.ConsciousnessStateAggregator._load_qualia", return_value=entries):
        snap = aggregate()
    assert not snap.phi_available
