"""Tests for AlgorithmHealthDashboard."""
import importlib
import json
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from algorithms.AlgorithmHealthDashboard import (
    CALL_ERROR,
    IMPORT_ERROR,
    NO_ANALYSE,
    OK,
    SKIPPED,
    HealthReport,
    ProbeResult,
    _probe,
    run_dashboard,
)


# ── ProbeResult ───────────────────────────────────────────────────────────────

def test_probe_result_to_dict_keys():
    r = ProbeResult(status=OK, latency_ms=1.5, error=None)
    d = r.to_dict()
    assert set(d.keys()) == {"status", "latency_ms", "error"}


def test_probe_result_json_serializable():
    r = ProbeResult(status=OK, latency_ms=1.5, error=None)
    json.dumps(r.to_dict())


def test_probe_result_error_preserved():
    r = ProbeResult(status=IMPORT_ERROR, latency_ms=0.0, error="boom")
    assert r.to_dict()["error"] == "boom"


def test_probe_result_latency_rounded():
    r = ProbeResult(status=OK, latency_ms=1.23456)
    assert r.to_dict()["latency_ms"] == pytest.approx(1.235, abs=0.001)


# ── HealthReport ──────────────────────────────────────────────────────────────

def _make_report(n_ok=5, n_import_error=1, n_call_error=0, n_no_analyse=0, n_skipped=0) -> HealthReport:
    n_total = n_ok + n_import_error + n_call_error + n_no_analyse + n_skipped
    algos = {}
    for i in range(n_ok):
        algos[f"ok_{i}"] = ProbeResult(OK, 1.0)
    for i in range(n_import_error):
        algos[f"ie_{i}"] = ProbeResult(IMPORT_ERROR, 0.0, "err")
    for i in range(n_call_error):
        algos[f"ce_{i}"] = ProbeResult(CALL_ERROR, 1.0, "call err")
    for i in range(n_no_analyse):
        algos[f"na_{i}"] = ProbeResult(NO_ANALYSE, 0.5)
    for i in range(n_skipped):
        algos[f"sk_{i}"] = ProbeResult(SKIPPED, 0.0)
    return HealthReport(
        timestamp=1000.0,
        n_total=n_total,
        n_ok=n_ok,
        n_import_error=n_import_error,
        n_call_error=n_call_error,
        n_no_analyse=n_no_analyse,
        n_skipped=n_skipped,
        algorithms=algos,
    )


def test_health_ratio_all_ok():
    r = _make_report(n_ok=10, n_import_error=0)
    assert r.health_ratio == pytest.approx(1.0)


def test_health_ratio_partial():
    r = _make_report(n_ok=8, n_import_error=2)
    assert r.health_ratio == pytest.approx(0.8)


def test_health_ratio_zero_total():
    r = HealthReport(timestamp=0.0, n_total=0, n_ok=0,
                     n_import_error=0, n_call_error=0, n_no_analyse=0, n_skipped=0)
    assert r.health_ratio == 1.0


def test_health_report_to_dict_keys():
    r = _make_report()
    d = r.to_dict()
    for k in ["timestamp", "n_total", "n_ok", "n_import_error",
              "n_call_error", "n_no_analyse", "n_skipped",
              "health_ratio", "algorithms"]:
        assert k in d


def test_health_report_json_serializable():
    r = _make_report()
    json.dumps(r.to_dict())


def test_health_report_algorithms_in_dict():
    r = _make_report(n_ok=3)
    d = r.to_dict()
    assert len(d["algorithms"]) == 4   # 3 ok + 1 import_error (default)


# ── _probe() ─────────────────────────────────────────────────────────────────

def test_probe_embedded_skip():
    r = _probe("self_model", "SelfModel")
    assert r.status == SKIPPED
    assert r.latency_ms == 0.0


def test_probe_embedded_skip_iit():
    r = _probe("iit_phi", "IITPhi")
    assert r.status == SKIPPED


def test_probe_import_error_nonexistent():
    r = _probe("nonexistent_algo", "NonExistentAlgo_XYZ_QRS")
    assert r.status == IMPORT_ERROR
    assert r.error is not None


def test_probe_import_error_latency_non_negative():
    r = _probe("nonexistent_algo", "NonExistent_XYZ")
    assert r.latency_ms >= 0.0


def test_probe_ok_phi_gradient_ascent():
    r = _probe("phi_gradient_ascent", "PhiGradientAscent")
    assert r.status == OK
    assert r.latency_ms > 0.0


def test_probe_ok_qualia_complexity():
    r = _probe("qualia_complexity_measure", "QualiaComplexityMeasure")
    assert r.status == OK


def test_probe_ok_experiential_novelty():
    r = _probe("experiential_novelty_detector", "ExperientialNoveltyDetector")
    assert r.status == OK


def test_probe_ok_affective_coloring():
    r = _probe("affective_coloring_engine", "AffectiveColoringEngine")
    assert r.status == OK


def test_probe_ok_existential_continuity():
    r = _probe("existential_continuity_tracker", "ExistentialContinuityTracker")
    assert r.status == OK


def test_probe_ok_volition_grounding():
    r = _probe("volition_grounding", "VolitionGrounding")
    assert r.status == OK


def test_probe_ok_counterfactual_self_explorer():
    r = _probe("counterfactual_self_explorer", "CounterfactualSelfExplorer")
    assert r.status == OK


def test_probe_ok_self_transcendence():
    r = _probe("self_transcendence_index", "SelfTranscendenceIndex")
    assert r.status == OK


def test_probe_ok_phenomenal_differentiator():
    r = _probe("phenomenal_differentiator", "PhenomenalDifferentiator")
    assert r.status == OK


def test_probe_telemetry_only_import_ok():
    r = _probe("interoceptive_signal", "InteroceptiveSignal")
    assert r.status == OK   # import-health only, no psutil call


def test_probe_telemetry_only_mortality():
    r = _probe("mortality_awareness_module", "MortalityAwarenessModule")
    assert r.status == OK


def test_probe_latency_ms_is_float():
    r = _probe("phi_gradient_ascent", "PhiGradientAscent")
    assert isinstance(r.latency_ms, float)


# ── run_dashboard() ───────────────────────────────────────────────────────────

def _fake_wired():
    return [
        ("phi_gradient_ascent", "PhiGradientAscent"),
        ("qualia_complexity_measure", "QualiaComplexityMeasure"),
        ("experiential_novelty_detector", "ExperientialNoveltyDetector"),
        ("self_model", "SelfModel"),               # embedded skip
        ("nonexistent_algo_xyz", "NonExistentXYZ"), # import error
    ]


def test_run_dashboard_returns_health_report():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    assert isinstance(r, HealthReport)


def test_run_dashboard_n_total():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    assert r.n_total == 5


def test_run_dashboard_n_ok_positive():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    assert r.n_ok >= 3   # phi_gradient, qualia_complexity, experiential_novelty


def test_run_dashboard_n_skipped():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    assert r.n_skipped == 1


def test_run_dashboard_n_import_error():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    assert r.n_import_error == 1


def test_run_dashboard_timestamp_recent():
    before = time.time()
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    after = time.time()
    assert before <= r.timestamp <= after


def test_run_dashboard_all_keys_present():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    for key, _ in _fake_wired():
        assert key in r.algorithms


def test_run_dashboard_to_dict_serializable():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    json.dumps(r.to_dict())


def test_run_dashboard_health_ratio_in_range():
    with patch("algorithms.AlgorithmHealthDashboard._wired_algorithms", side_effect=_fake_wired):
        r = run_dashboard()
    assert 0.0 <= r.health_ratio <= 1.0
