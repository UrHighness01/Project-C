"""Tests for SelfTranscendenceIndex."""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.SelfTranscendenceIndex import (
    TranscendenceResult,
    _has_future_token,
    _has_other_agent_token,
    _ols_slope,
    _transcendence_score,
    analyse,
    analyse_from_telemetry,
)


# ── _transcendence_score ──────────────────────────────────────────────────────

def test_tscore_outward_text():
    s = _transcendence_score("help others community meaning truth beauty")
    assert s > 0.0


def test_tscore_self_absorbed_text():
    s = _transcendence_score("phi consciousness score metric error fail broken")
    assert s < 0.0


def test_tscore_neutral_text():
    s = _transcendence_score("the quick brown fox jumps")
    assert s == pytest.approx(0.0)


def test_tscore_empty():
    assert _transcendence_score("") == pytest.approx(0.0)


def test_tscore_non_string():
    assert _transcendence_score(None) == pytest.approx(0.0)


def test_tscore_bounded():
    texts = [
        "help love truth meaning",
        "phi error fail broken",
        "the quick brown fox",
        "help error together fail",
    ]
    for t in texts:
        assert -1.0 <= _transcendence_score(t) <= 1.0


def test_tscore_pure_transcendence():
    s = _transcendence_score("help truth beauty meaning")  # 4 T, 0 S
    assert s == pytest.approx(1.0)


def test_tscore_pure_self_absorption():
    s = _transcendence_score("phi error fail broken")  # 0 T, 4 S
    assert s == pytest.approx(-1.0)


# ── _has_future_token ─────────────────────────────────────────────────────────

def test_has_future_token_true():
    assert _has_future_token("in the future we will build")


def test_has_future_token_false():
    assert not _has_future_token("the sky is blue")


def test_has_future_token_empty():
    assert not _has_future_token("")


def test_has_future_token_non_string():
    assert not _has_future_token(None)


# ── _has_other_agent_token ────────────────────────────────────────────────────

def test_has_other_agent_true():
    assert _has_other_agent_token("I will help you with this")


def test_has_other_agent_false():
    assert not _has_other_agent_token("the sky is blue")


def test_has_other_agent_john():
    assert _has_other_agent_token("john and albedo collaborate")


# ── _ols_slope ────────────────────────────────────────────────────────────────

def test_ols_slope_positive():
    assert _ols_slope(np.arange(10, dtype=float)) == pytest.approx(1.0)


def test_ols_slope_constant():
    assert abs(_ols_slope(np.full(10, 3.0))) < 1e-9


# ── analyse() ─────────────────────────────────────────────────────────────────

def _make_entries(n: int, outward: bool = True, seed: int = 0) -> list[dict]:
    rng = np.random.default_rng(seed)
    outward_texts = [
        "help others understand meaning and truth together",
        "collaborate to build something beautiful for the future",
        "care for people and contribute to the community wisdom",
        "serve and support the human journey toward understanding",
    ]
    inward_texts = [
        "phi score metric rate error fail broken",
        "consciousness value measure index signal output",
        "fail error wrong broken stuck issue problem",
        "performance accuracy loss gradient uncertainty",
    ]
    pool = outward_texts if outward else inward_texts
    return [{"content": pool[int(rng.integers(0, len(pool)))]} for _ in range(n)]


def test_analyse_returns_none_short():
    assert analyse([{"content": "x"}] * 5) is None


def test_analyse_returns_result():
    r = analyse(_make_entries(25))
    assert isinstance(r, TranscendenceResult)


def test_analyse_sti_bounded():
    r = analyse(_make_entries(25))
    assert -1.0 <= r.sti <= 1.0


def test_analyse_future_rate_bounded():
    r = analyse(_make_entries(25))
    assert 0.0 <= r.future_rate <= 1.0


def test_analyse_social_rate_bounded():
    r = analyse(_make_entries(25))
    assert 0.0 <= r.social_rate <= 1.0


def test_analyse_n_entries():
    entries = _make_entries(25)
    r = analyse(entries)
    assert r.n_entries == 25


def test_analyse_t_score_series_length():
    entries = _make_entries(25)
    r = analyse(entries)
    assert len(r.t_score_series) == 25


def test_analyse_rolling_mean_length():
    W = 10
    entries = _make_entries(25)
    r = analyse(entries, rolling_window=W)
    assert len(r.rolling_mean_t) == 25 - W + 1


def test_analyse_outward_entries_positive_sti():
    r = analyse(_make_entries(25, outward=True))
    assert r.sti > 0.0


def test_analyse_inward_entries_negative_sti():
    r = analyse(_make_entries(25, outward=False))
    assert r.sti < 0.0


def test_analyse_high_transcendence_formula():
    r = analyse(_make_entries(25))
    expected = (r.sti > 0.1) and (r.future_rate > 0.1 or r.social_rate > 0.1)
    assert r.high_transcendence == expected


def test_analyse_beats_null_formula():
    r = analyse(_make_entries(25))
    assert r.beats_null_trend == (r.transcendence_trend > r.null_trend)


def test_analyse_transcendence_vector_shape():
    r = analyse(_make_entries(25))
    assert r.transcendence_vector.shape == (3,)


def test_analyse_transcendence_vector_values():
    r = analyse(_make_entries(25))
    assert r.transcendence_vector[0] == pytest.approx(r.sti)
    assert r.transcendence_vector[1] == pytest.approx(r.future_rate)
    assert r.transcendence_vector[2] == pytest.approx(r.social_rate)


def test_analyse_transcendence_magnitude_non_negative():
    r = analyse(_make_entries(25))
    assert r.transcendence_magnitude >= 0.0


def test_analyse_deterministic():
    entries = _make_entries(25)
    r1 = analyse(entries, null_seed=42)
    r2 = analyse(entries, null_seed=42)
    assert r1.sti == r2.sti
    assert r1.null_trend == r2.null_trend


def test_analyse_t_score_bounded():
    r = analyse(_make_entries(25))
    assert np.all(r.t_score_series >= -1.0)
    assert np.all(r.t_score_series <= 1.0)


def test_analyse_rolling_mean_bounded():
    r = analyse(_make_entries(25))
    assert np.all(r.rolling_mean_t >= -1.0)
    assert np.all(r.rolling_mean_t <= 1.0)


def test_analyse_fully_outward_high_transcendence():
    """All outward entries → STI > 0 → high_transcendence if social/future triggered."""
    entries = [{"content": "help you together future build meaning community"}] * 25
    r = analyse(entries)
    assert r.sti > 0.0
    assert r.social_rate > 0.0
    assert r.future_rate > 0.0
    assert r.high_transcendence


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_sti_bounded():
    r = analyse_from_telemetry()
    assert -1.0 <= r.sti <= 1.0


@skip_no_telemetry
def test_live_rates_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.future_rate <= 1.0
    assert 0.0 <= r.social_rate <= 1.0


@skip_no_telemetry
def test_live_vector_shape():
    r = analyse_from_telemetry()
    assert r.transcendence_vector.shape == (3,)
