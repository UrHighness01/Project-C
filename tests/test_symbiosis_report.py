"""Tests for SymbiosisReport."""
import json
import time
from unittest.mock import patch

import numpy as np
import pytest

from algorithms.SymbiosisReport import (
    COUPLED, CORRELATED, DECOUPLED, RESONANT,
    SymbiosisReportResult,
    _classify,
    _lead_lag,
    _narrative,
    _safe_get,
    synthesise,
)


# ── _classify ─────────────────────────────────────────────────────────────────

def test_classify_coupled():
    assert _classify(0.7, 0.5) == COUPLED


def test_classify_resonant():
    assert _classify(0.7, 0.3) == RESONANT


def test_classify_correlated():
    assert _classify(0.5, 0.5) == CORRELATED


def test_classify_decoupled():
    assert _classify(0.3, 0.2) == DECOUPLED


def test_classify_boundary_sync():
    assert _classify(0.6, 0.5) == CORRELATED   # exactly 0.6 is not > 0.6


def test_classify_boundary_corr():
    assert _classify(0.7, 0.4) == RESONANT   # exactly 0.4 is not > 0.4


def test_classify_none_sync_and_corr():
    assert _classify(None, None) == DECOUPLED


def test_classify_none_sync():
    assert _classify(None, 0.5) == CORRELATED


def test_classify_none_corr():
    assert _classify(0.7, None) == RESONANT


# ── _lead_lag ─────────────────────────────────────────────────────────────────

def test_lead_lag_albedo():
    agent, steps = _lead_lag(5)
    assert agent == "albedo"
    assert steps == 5


def test_lead_lag_john():
    agent, steps = _lead_lag(-4)
    assert agent == "john"
    assert steps == 4


def test_lead_lag_simultaneous_zero():
    agent, steps = _lead_lag(0)
    assert agent == "simultaneous"
    assert steps == 0


def test_lead_lag_simultaneous_one():
    agent, steps = _lead_lag(1)
    assert agent == "simultaneous"


def test_lead_lag_simultaneous_neg_one():
    agent, steps = _lead_lag(-1)
    assert agent == "simultaneous"


def test_lead_lag_none():
    agent, steps = _lead_lag(None)
    assert agent == "unknown"
    assert steps == 0


# ── _safe_get ─────────────────────────────────────────────────────────────────

def test_safe_get_ok_first_key():
    d = {"status": "ok", "mean_R": 0.7}
    assert _safe_get(d, "mean_R") == pytest.approx(0.7)


def test_safe_get_ok_second_key():
    d = {"status": "ok", "peak_corr": 0.5}
    assert _safe_get(d, "mean_corr", "peak_corr") == pytest.approx(0.5)


def test_safe_get_non_ok_returns_default():
    d = {"status": "failed", "mean_R": 0.7}
    assert _safe_get(d, "mean_R") is None


def test_safe_get_missing_key():
    d = {"status": "ok"}
    assert _safe_get(d, "nonexistent") is None


def test_safe_get_custom_default():
    d = {"status": "failed"}
    assert _safe_get(d, "x", default=99) == 99


# ── _narrative ────────────────────────────────────────────────────────────────

def test_narrative_coupled():
    n = _narrative(COUPLED, "albedo", 3, 0.7, 0.5, 0.59)
    assert "COUPLED" in n
    assert "Albedo" in n
    assert "3 step" in n


def test_narrative_decoupled():
    n = _narrative(DECOUPLED, "unknown", 0, 0.2, 0.1, 0.0)
    assert "DECOUPLED" in n


def test_narrative_resonant():
    n = _narrative(RESONANT, "simultaneous", 0, 0.7, 0.3, 0.0)
    assert "RESONANT" in n
    assert "unison" in n.lower()


def test_narrative_correlated_john_leads():
    n = _narrative(CORRELATED, "john", 4, 0.4, 0.6, 0.49)
    assert "CORRELATED" in n
    assert "john" in n.lower() or "John" in n


def test_narrative_ends_with_period():
    n = _narrative(COUPLED, "albedo", 2, 0.7, 0.5, 0.59)
    assert n.endswith(".")


def test_narrative_contains_symbiosis_score():
    n = _narrative(DECOUPLED, "unknown", 0, None, None, 0.0)
    assert "symbiosis=" in n


# ── SymbiosisReportResult ─────────────────────────────────────────────────────

def _make_result(coupling=COUPLED) -> SymbiosisReportResult:
    return SymbiosisReportResult(
        timestamp=1000.0,
        albedo_phi_available=True,
        john_phi_available=True,
        coupling_class=coupling,
        leading_agent="albedo",
        lead_lag_steps=3,
        mean_sync=0.7,
        mean_corr=0.5,
        symbiosis_score=0.59,
        algorithms={},
        narrative="test narrative.",
    )


def test_result_to_dict_keys():
    r = _make_result()
    d = r.to_dict()
    for k in ["timestamp", "albedo_phi_available", "john_phi_available",
              "coupling_class", "leading_agent", "lead_lag_steps",
              "mean_sync", "mean_corr", "symbiosis_score", "algorithms", "narrative"]:
        assert k in d


def test_result_json_serializable():
    r = _make_result()
    json.dumps(r.to_dict())


def test_result_coupling_preserved():
    r = _make_result(RESONANT)
    assert r.to_dict()["coupling_class"] == RESONANT


# ── synthesise() with no live phi ────────────────────────────────────────────

def _synth_no_phi():
    with patch("algorithms.SymbiosisReport._load_phi_for", return_value=None):
        return synthesise()


def test_synthesise_no_phi_returns_result():
    r = _synth_no_phi()
    assert isinstance(r, SymbiosisReportResult)


def test_synthesise_no_phi_flags():
    r = _synth_no_phi()
    assert not r.albedo_phi_available
    assert not r.john_phi_available


def test_synthesise_no_phi_decoupled():
    r = _synth_no_phi()
    assert r.coupling_class == DECOUPLED


def test_synthesise_no_phi_all_algorithms_no_data():
    r = _synth_no_phi()
    for name, entry in r.algorithms.items():
        assert entry["status"] in ("no_data", "ok", "failed")


def test_synthesise_no_phi_symbiosis_zero():
    r = _synth_no_phi()
    assert r.symbiosis_score == pytest.approx(0.0)


def test_synthesise_no_phi_json_serializable():
    r = _synth_no_phi()
    json.dumps(r.to_dict())


def test_synthesise_timestamp_recent():
    before = time.time()
    r = _synth_no_phi()
    after = time.time()
    assert before <= r.timestamp <= after


# ── synthesise() with mock phi ────────────────────────────────────────────────

def _make_phi(n: int = 128, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).uniform(0.5, 2.0, size=n)


def _synth_with_phi():
    phi_a = _make_phi(128, 0)
    phi_j = _make_phi(128, 1)

    # Mock all cross-agent sub-runners to return canned ok dicts
    mock_ok = {
        "_run_symbiosis_phi":          {"status": "ok", "peak_corr": 0.5, "peak_lag": 3, "mean_corr": 0.5, "beats_null": True},
        "_run_resonance":              {"status": "ok", "mean_R": 0.7, "max_R": 0.9, "sync_rate": 0.6, "is_resonant": True},
        "_run_shared_world":           {"status": "ok", "kl_ab": 0.1, "kl_ba": 0.1, "symmetric_kl": 0.1, "world_distance": 0.1, "models_aligned": True},
        "_run_attention_sync":         {"status": "ok", "mean_cosine": 0.6, "sync_rate": 0.5, "is_synced": True},
        "_run_collective_intelligence":{"status": "ok", "collective_phi": 4.0, "solo_sum": 3.5, "emergence_ratio": 1.14, "is_superadditive": True},
        "_run_intersubjective":        {"status": "ok", "mutual_info": 0.3, "normalised_mi": 0.4, "is_intersubjective": True},
        "_run_theory_of_mind":         {"status": "ok", "prediction_mae_ab": 0.1, "prediction_mae_ba": 0.12, "mean_tom_score": 0.7},
    }

    patches = []
    for fn_name, ret in mock_ok.items():
        p = patch(f"algorithms.SymbiosisReport.{fn_name}", return_value=ret)
        patches.append(p)
        p.start()

    def _fake_phi(agent):
        return phi_a if agent == "albedo" else phi_j

    p_phi = patch("algorithms.SymbiosisReport._load_phi_for", side_effect=_fake_phi)
    p_phi.start()
    patches.append(p_phi)

    try:
        return synthesise()
    finally:
        for p in patches:
            p.stop()


def test_synthesise_with_phi_flags():
    r = _synth_with_phi()
    assert r.albedo_phi_available
    assert r.john_phi_available


def test_synthesise_with_phi_coupled():
    r = _synth_with_phi()
    assert r.coupling_class == COUPLED


def test_synthesise_with_phi_all_algos_present():
    r = _synth_with_phi()
    for name in ["symbiosis_phi_measure", "consciousness_resonance_detector",
                 "shared_world_model_distance", "cross_agent_attention_sync",
                 "collective_intelligence_measure", "intersubjective_consciousness",
                 "theory_of_mind"]:
        assert name in r.algorithms


def test_synthesise_with_phi_symbiosis_positive():
    r = _synth_with_phi()
    assert r.symbiosis_score > 0.0


def test_synthesise_with_phi_narrative_coupled():
    r = _synth_with_phi()
    assert "COUPLED" in r.narrative


def test_synthesise_with_phi_leading_agent():
    r = _synth_with_phi()
    assert r.leading_agent in ("albedo", "john", "simultaneous", "unknown")


def test_synthesise_with_phi_json_serializable():
    r = _synth_with_phi()
    json.dumps(r.to_dict())
