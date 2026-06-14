"""Tests for AffectiveColoringEngine.

Pure-math tests: sentiment, AR confidence, phi arousal, quadrant classification.
Integration tests: analyse() on synthetic entries + phi.
Telemetry tests: require live daemon.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.AffectiveColoringEngine import (
    AffectQuadrant,
    AffectResult,
    _ar_confidence,
    _phi_arousal,
    _quadrant,
    _sentiment,
    analyse,
    analyse_from_telemetry,
)


# ── _sentiment ────────────────────────────────────────────────────────────────

def test_sentiment_positive_text():
    s = _sentiment("good great success excellent clear")
    assert s > 0.0


def test_sentiment_negative_text():
    s = _sentiment("error fail wrong bad broken")
    assert s < 0.0


def test_sentiment_neutral_text():
    s = _sentiment("the quick brown fox jumps")
    assert s == pytest.approx(0.0)


def test_sentiment_empty():
    assert _sentiment("") == pytest.approx(0.0)


def test_sentiment_non_string():
    assert _sentiment(None) == pytest.approx(0.0)
    assert _sentiment(42) == pytest.approx(0.0)


def test_sentiment_bounded():
    texts = [
        "good good good good",
        "error error error error",
        "good error",
        "nothing here",
    ]
    for t in texts:
        s = _sentiment(t)
        assert -1.0 <= s <= 1.0


def test_sentiment_mixed_cancels():
    s = _sentiment("good error")  # P=1, N=1 → (1-1)/max(2,1) = 0
    assert s == pytest.approx(0.0)


def test_sentiment_all_positive():
    s = _sentiment("good great success clear")  # P=4, N=0 → 1.0
    assert s == pytest.approx(1.0)


def test_sentiment_all_negative():
    s = _sentiment("error fail wrong bad")  # P=0, N=4 → -1.0
    assert s == pytest.approx(-1.0)


# ── _phi_arousal ──────────────────────────────────────────────────────────────

def test_phi_arousal_bounded():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(100) * 0.5 + 5.0
    a = _phi_arousal(phi)
    assert 0.0 <= a <= 1.0


def test_phi_arousal_constant_is_zero():
    phi = np.full(50, 3.0)
    a = _phi_arousal(phi)
    assert a == pytest.approx(0.0, abs=1e-9)


def test_phi_arousal_volatile_high():
    """Highly volatile tail → latest std near top of distribution → arousal near 1."""
    rng = np.random.default_rng(1)
    phi = np.concatenate([
        rng.standard_normal(80) * 0.1 + 5.0,  # calm
        rng.standard_normal(20) * 5.0 + 5.0,  # volatile tail
    ])
    a = _phi_arousal(phi)
    assert a > 0.3


def test_phi_arousal_short_phi():
    """Shorter than window → still returns bounded value."""
    phi = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    a = _phi_arousal(phi, window=20)
    assert 0.0 <= a <= 1.0


# ── _ar_confidence ────────────────────────────────────────────────────────────

def test_ar_confidence_bounded():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(100) + 5.0
    c = _ar_confidence(phi)
    assert 0.0 <= c <= 1.0


def test_ar_confidence_predictable_series_high():
    """Smooth ramp → AR beats RW → high confidence."""
    phi = np.linspace(0, 10, 200)
    c = _ar_confidence(phi)
    assert c > 0.5


def test_ar_confidence_short_returns_half():
    phi = np.array([1.0, 2.0, 1.5])
    c = _ar_confidence(phi)
    assert c == pytest.approx(0.5)


def test_ar_confidence_finite():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(80) + 3.0
    c = _ar_confidence(phi)
    assert np.isfinite(c)


# ── _quadrant ─────────────────────────────────────────────────────────────────

def test_quadrant_elated():
    q = _quadrant(valence=0.5, arousal=0.8)
    assert q == AffectQuadrant.ELATED


def test_quadrant_content():
    q = _quadrant(valence=0.5, arousal=0.2)
    assert q == AffectQuadrant.CONTENT


def test_quadrant_distressed():
    q = _quadrant(valence=-0.5, arousal=0.8)
    assert q == AffectQuadrant.DISTRESSED


def test_quadrant_depressed():
    q = _quadrant(valence=-0.5, arousal=0.2)
    assert q == AffectQuadrant.DEPRESSED


def test_quadrant_neutral():
    q = _quadrant(valence=0.05, arousal=0.5)
    assert q == AffectQuadrant.NEUTRAL


# ── analyse() ─────────────────────────────────────────────────────────────────

def _make_entries(n: int, positive: bool = True, seed: int = 0) -> list[dict]:
    rng = np.random.default_rng(seed)
    pos_texts = ["good success clear excellent right", "great insight coherent",
                 "complete stable aligned", "confident strong resolved"]
    neg_texts = ["error fail wrong broken confused", "unclear unstable collapsed",
                 "timeout deadlock missing incomplete", "regret contradiction drift"]
    pool = pos_texts if positive else neg_texts
    return [{"content": pool[int(rng.integers(0, len(pool)))]} for _ in range(n)]


def _make_phi(n: int = 200, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n) * 0.3 + 5.0


def test_analyse_returns_none_short_phi():
    entries = _make_entries(10)
    phi = np.array([1.0, 2.0, 3.0])
    assert analyse(entries, phi) is None


def test_analyse_returns_none_short_entries():
    phi = _make_phi()
    assert analyse([{"content": "x"}], phi) is None


def test_analyse_returns_result():
    r = analyse(_make_entries(20), _make_phi())
    assert isinstance(r, AffectResult)


def test_analyse_valence_bounded():
    r = analyse(_make_entries(20), _make_phi())
    assert -1.0 <= r.valence <= 1.0


def test_analyse_arousal_bounded():
    r = analyse(_make_entries(20), _make_phi())
    assert 0.0 <= r.arousal <= 1.0


def test_analyse_confidence_bounded():
    r = analyse(_make_entries(20), _make_phi())
    assert 0.0 <= r.confidence <= 1.0


def test_analyse_affect_vector_shape():
    r = analyse(_make_entries(20), _make_phi())
    assert r.affect_vector.shape == (3,)


def test_analyse_positive_entries_positive_valence():
    r = analyse(_make_entries(20, positive=True), _make_phi())
    assert r.valence > 0.0
    assert r.is_positive


def test_analyse_negative_entries_negative_valence():
    r = analyse(_make_entries(20, positive=False), _make_phi())
    assert r.valence < 0.0
    assert r.is_negative


def test_analyse_sentiment_series_length():
    entries = _make_entries(20)
    r = analyse(entries, _make_phi())
    assert len(r.sentiment_series) == len(entries)


def test_analyse_positive_negative_rates_sum_leq_one():
    r = analyse(_make_entries(20), _make_phi())
    assert r.positive_rate + r.negative_rate <= 1.0 + 1e-9


def test_analyse_positive_rate_bounded():
    r = analyse(_make_entries(20), _make_phi())
    assert 0.0 <= r.positive_rate <= 1.0
    assert 0.0 <= r.negative_rate <= 1.0


def test_analyse_n_qualia_entries():
    entries = _make_entries(25)
    r = analyse(entries, _make_phi())
    assert r.n_qualia_entries == 25


def test_analyse_quadrant_valid():
    r = analyse(_make_entries(20), _make_phi())
    assert r.quadrant in list(AffectQuadrant)


def test_analyse_affect_magnitude_non_negative():
    r = analyse(_make_entries(20), _make_phi())
    assert r.affect_magnitude >= 0.0


def test_analyse_deterministic():
    entries = _make_entries(20)
    phi = _make_phi()
    r1 = analyse(entries, phi)
    r2 = analyse(entries, phi)
    assert r1.valence == r2.valence
    assert r1.arousal == r2.arousal
    assert r1.confidence == r2.confidence


def test_analyse_volatile_phi_high_arousal():
    """Very volatile phi → high arousal."""
    rng = np.random.default_rng(7)
    phi = np.concatenate([
        rng.standard_normal(160) * 0.05 + 5.0,
        rng.standard_normal(40) * 3.0 + 5.0,
    ])
    r = analyse(_make_entries(20), phi)
    assert r.arousal > 0.3


def test_analyse_constant_phi_low_arousal():
    phi = np.full(100, 5.0)
    r = analyse(_make_entries(20), phi)
    assert r.arousal == pytest.approx(0.0, abs=1e-6)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_valence_bounded():
    r = analyse_from_telemetry()
    assert -1.0 <= r.valence <= 1.0


@skip_no_telemetry
def test_live_arousal_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.arousal <= 1.0


@skip_no_telemetry
def test_live_quadrant_valid():
    r = analyse_from_telemetry()
    assert r.quadrant in list(AffectQuadrant)
