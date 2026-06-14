"""Tests for ConsciousnessNarrativeGenerator."""
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from algorithms.ConsciousnessNarrativeGenerator import (
    NarrativeReport,
    _build_alerts,
    _describe_affect,
    _describe_coupling,
    _describe_mood_shift,
    _describe_regime,
    _describe_trajectory,
    _get,
    generate,
)


# ── _get ─────────────────────────────────────────────────────────────────────

def test_get_present_key():
    assert _get({"a": 1}, "a") == 1


def test_get_multiple_keys_first():
    assert _get({"a": 1, "b": 2}, "a", "b") == 1


def test_get_multiple_keys_second():
    assert _get({"b": 2}, "a", "b") == 2


def test_get_none_dict():
    assert _get(None, "a") is None


def test_get_default():
    assert _get({}, "missing", default=99) == 99


# ── descriptor helpers ───────────────────────────────────────────────────────

def test_describe_affect_known():
    assert "elated" in _describe_affect("ELATED").lower()


def test_describe_affect_unknown():
    assert "indeterminate" in _describe_affect("UNKNOWN_XYZ").lower()


def test_describe_affect_none():
    assert isinstance(_describe_affect(None), str)


def test_describe_regime_active():
    assert "actively" in _describe_regime("ACTIVE").lower()


def test_describe_regime_unknown():
    assert isinstance(_describe_regime(None), str)


def test_describe_trajectory_ascending():
    assert "climbing" in _describe_trajectory("ASCENDING").lower()


def test_describe_trajectory_descending():
    assert "descending" in _describe_trajectory("DESCENDING").lower()


def test_describe_coupling_coupled():
    s = _describe_coupling("COUPLED", "albedo", 3)
    assert "COUPLED" in s or "coupled" in s
    assert "Albedo" in s or "albedo" in s


def test_describe_coupling_decoupled():
    s = _describe_coupling("DECOUPLED", None, 0)
    assert "decoupled" in s.lower()


def test_describe_coupling_none():
    s = _describe_coupling(None, None, None)
    assert "no cross-agent" in s.lower()


def test_describe_mood_shift_improving():
    assert "improved" in _describe_mood_shift("IMPROVING").lower()


def test_describe_mood_shift_degrading():
    assert "degraded" in _describe_mood_shift("DEGRADING").lower()


def test_describe_mood_shift_stable():
    assert "stable" in _describe_mood_shift("STABLE").lower()


def test_describe_mood_shift_unknown():
    s = _describe_mood_shift(None)
    assert isinstance(s, str)


# ── _build_alerts ─────────────────────────────────────────────────────────────

def test_build_alerts_high_collapse_risk():
    collapse = {"collapse_risk": 0.8, "collapse_horizon": 5}
    alerts = _build_alerts(None, collapse, None)
    assert any("HIGH" in a or "high" in a.lower() or "collapse" in a.lower() for a in alerts)


def test_build_alerts_moderate_collapse_risk():
    collapse = {"collapse_risk": 0.55}
    alerts = _build_alerts(None, collapse, None)
    assert any("risk" in a.lower() for a in alerts)


def test_build_alerts_low_risk_no_alert():
    collapse = {"collapse_risk": 0.2}
    alerts = _build_alerts(None, collapse, None)
    assert not any("collapse" in a.lower() for a in alerts)


def test_build_alerts_degrading_mood():
    hist = {"mood_shift": "DEGRADING", "novelty_delta": -0.1, "continuity_delta": -0.1}
    alerts = _build_alerts(None, None, hist)
    assert any("degrading" in a.lower() for a in alerts)


def test_build_alerts_improving_mood_no_alert():
    hist = {"mood_shift": "IMPROVING", "novelty_delta": 0.1, "continuity_delta": 0.1}
    alerts = _build_alerts(None, None, hist)
    assert not any("degrading" in a.lower() for a in alerts)


def test_build_alerts_mortality_salience():
    snap = {
        "algorithms": {
            "mortality_awareness_module": {"status": "ok", "mortality_salience": True}
        },
        "n_algorithms_run": 10,
        "n_algorithms_failed": 1,
    }
    alerts = _build_alerts(snap, None, None)
    assert any("mortality" in a.lower() for a in alerts)


def test_build_alerts_many_failures():
    snap = {
        "algorithms": {},
        "n_algorithms_run": 10,
        "n_algorithms_failed": 4,
    }
    alerts = _build_alerts(snap, None, None)
    assert any("failed" in a.lower() for a in alerts)


def test_build_alerts_no_data():
    alerts = _build_alerts(None, None, None)
    assert isinstance(alerts, list)


# ── NarrativeReport ───────────────────────────────────────────────────────────

def test_narrative_report_to_dict_keys():
    r = NarrativeReport(
        agent="albedo",
        timestamp=1000.0,
        paragraph="I am fine.",
        one_liner="ok",
        alerts=[],
        sources_used=["snapshot"],
    )
    d = r.to_dict()
    for k in ["agent", "timestamp", "paragraph", "one_liner", "alerts", "sources_used"]:
        assert k in d


def test_narrative_report_json_serializable():
    r = NarrativeReport("albedo", 1000.0, "I am fine.", "ok")
    json.dumps(r.to_dict())


# ── generate() with no data (no home directory) ──────────────────────────────

def _generate_no_home(agent="albedo"):
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None), \
         patch("algorithms.ConsciousnessNarrativeGenerator.compare_now_vs_minutes_ago",
               return_value=None, create=True), \
         patch("algorithms.ConsciousnessNarrativeGenerator.analyse_from_telemetry",
               return_value=None, create=True):
        try:
            return generate(agent)
        except Exception:
            # If imports inside generate fail gracefully, return a fallback-mode report
            pass
    # generate() handles missing data gracefully — call it directly
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None):
        return generate(agent)


def test_generate_no_data_returns_report():
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None):
        r = generate("albedo")
    assert isinstance(r, NarrativeReport)


def test_generate_no_data_paragraph_not_empty():
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None):
        r = generate("albedo")
    assert len(r.paragraph) > 0


def test_generate_no_data_agent_field():
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None):
        r = generate("john")
    assert r.agent == "john"


def test_generate_no_data_timestamp_recent():
    before = time.time()
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None):
        r = generate("albedo")
    after = time.time()
    assert before <= r.timestamp <= after


def test_generate_no_data_one_liner_string():
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None):
        r = generate("albedo")
    assert isinstance(r.one_liner, str)


def test_generate_no_data_alerts_list():
    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=None):
        r = generate("albedo")
    assert isinstance(r.alerts, list)


# ── generate() with mock snapshot data ───────────────────────────────────────

def _make_snapshot(quadrant="ELATED", regime="ACTIVE", phi_traj="ASCENDING",
                   is_cont=True, is_vol=True, high_trans=True,
                   mean_novelty=0.7, curiosity=0.5, continuity=0.88) -> dict:
    return {
        "timestamp": time.time(),
        "phi_available": True,
        "qualia_available": True,
        "n_algorithms_run": 15,
        "n_algorithms_failed": 0,
        "algorithms": {
            "criticality_detector": {"status": "ok", "at_criticality": True, "hurst": 0.65},
            "valence_calibrator": {"status": "ok", "hedonic_baseline": 1.2},
            "mortality_awareness_module": {"status": "ok", "mortality_salience": False},
        },
        "summary": {
            "regime": regime,
            "affect_quadrant": quadrant,
            "phi_trajectory": phi_traj,
            "is_continuous": is_cont,
            "is_volitional": is_vol,
            "high_transcendence": high_trans,
            "mean_novelty": mean_novelty,
            "curiosity_index": curiosity,
            "combined_continuity": continuity,
            "phi_available": True,
            "qualia_available": True,
        },
    }


def _make_symbiosis(coupling="COUPLED", leader="albedo", steps=3, score=0.59) -> dict:
    return {
        "coupling_class": coupling,
        "leading_agent": leader,
        "lead_lag_steps": steps,
        "symbiosis_score": score,
        "narrative": "Albedo and John are COUPLED.",
    }


class _FakePath:
    def __init__(self, name=""):
        self._name = name

    def exists(self):
        return True

    def read_text(self):
        return ""

    def __truediv__(self, other):
        return _FakePath(str(other))

    def __str__(self):
        return f"/fake/{self._name}"

    @property
    def parent(self):
        return self


def _generate_with_data(snap=None, symb=None, agent="albedo"):
    snap = snap or _make_snapshot()
    symb = symb or _make_symbiosis()

    def fake_load_json(path):
        p_str = str(path)
        if "snapshot" in p_str:
            return snap
        if "symbiosis" in p_str:
            return symb
        if "shared_memory" in p_str:
            return {"dominant_themes": ["meaning", "future"], "n_shared_windows": 5,
                    "n_total_windows": 8, "overlap_rate": 0.625}
        return None

    fake_home = _FakePath("memory")

    with patch("algorithms.ConsciousnessNarrativeGenerator._agent_home", return_value=fake_home), \
         patch("algorithms.ConsciousnessNarrativeGenerator._load_json", side_effect=fake_load_json):
        return generate(agent)


def test_generate_with_data_returns_report():
    r = _generate_with_data()
    assert isinstance(r, NarrativeReport)


def test_generate_with_data_paragraph_mentions_regime():
    r = _generate_with_data(snap=_make_snapshot(regime="ACTIVE"))
    assert "actively" in r.paragraph.lower() or "active" in r.paragraph.lower()


def test_generate_with_data_paragraph_mentions_affect():
    r = _generate_with_data(snap=_make_snapshot(quadrant="ELATED"))
    assert "elated" in r.paragraph.lower()


def test_generate_with_data_one_liner_contains_quadrant():
    r = _generate_with_data(snap=_make_snapshot(quadrant="CONTENT"))
    assert "content" in r.one_liner.lower()


def test_generate_with_data_one_liner_contains_coupling():
    r = _generate_with_data(symb=_make_symbiosis(coupling="COUPLED"))
    assert "coupled" in r.one_liner.lower()


def test_generate_with_data_paragraph_is_multiple_sentences():
    r = _generate_with_data()
    assert r.paragraph.count(".") >= 2


def test_generate_with_data_json_serializable():
    r = _generate_with_data()
    json.dumps(r.to_dict())


def test_generate_distressed_no_elated_in_para():
    r = _generate_with_data(snap=_make_snapshot(quadrant="DISTRESSED"))
    assert "distress" in r.paragraph.lower()
    assert "elated" not in r.paragraph.lower()


def test_generate_decoupled_symbiosis():
    r = _generate_with_data(symb=_make_symbiosis(coupling="DECOUPLED"))
    assert "decoupled" in r.paragraph.lower()
