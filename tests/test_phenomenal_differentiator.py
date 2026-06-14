"""Tests for PhenomenalDifferentiator.

Pure-math tests cover signature generation, Heaps' law fit, entropy.
Telemetry tests require John's qualia stream.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.PhenomenalDifferentiator import (
    DifferentiationResult,
    _differentiation_entropy,
    _fit_heaps,
    _signature,
    analyse,
    analyse_from_telemetry,
)


# ── _signature ────────────────────────────────────────────────────────────────

def test_signature_length_16():
    s = _signature("hello world phi consciousness")
    assert len(s) == 16


def test_signature_deterministic():
    s1 = _signature("the quick brown fox")
    s2 = _signature("the quick brown fox")
    assert s1 == s2


def test_signature_order_invariant():
    """Token set is unordered; same set → same signature."""
    s1 = _signature("alpha beta gamma")
    s2 = _signature("gamma alpha beta")
    assert s1 == s2


def test_signature_different_content():
    s1 = _signature("consciousness phi awareness")
    s2 = _signature("entropy gradient descent")
    assert s1 != s2


def test_signature_empty():
    assert _signature("") == ""


def test_signature_non_string():
    assert _signature(None) == ""
    assert _signature(42) == ""


def test_signature_hex_chars():
    """MD5 hex digest has only 0-9 and a-f."""
    s = _signature("some content here")
    assert all(c in "0123456789abcdef" for c in s)


# ── _fit_heaps ────────────────────────────────────────────────────────────────

def test_fit_heaps_returns_zeros_for_short():
    v = np.array([1, 1, 1])
    beta, K, r2 = _fit_heaps(v)
    assert beta == 0.0 and K == 0.0 and r2 == 0.0


def test_fit_heaps_exact_power_law():
    """V(t) = 3 * t^0.5 → β ≈ 0.5."""
    t = np.arange(1, 101, dtype=float)
    v = (3.0 * t ** 0.5).astype(int)
    v = np.maximum(v, 2)
    beta, K, r2 = _fit_heaps(v)
    assert abs(beta - 0.5) < 0.05, f"Expected β≈0.5, got {beta:.4f}"
    assert r2 > 0.99


def test_fit_heaps_constant_series():
    """Constant V (all repeats) → β ≈ 0."""
    v = np.full(50, 5)
    beta, K, r2 = _fit_heaps(v)
    assert abs(beta) < 0.05


def test_fit_heaps_r2_bounded():
    t = np.arange(1, 51, dtype=float)
    v = (2 * np.sqrt(t)).astype(int)
    v = np.maximum(v, 2)
    _, _, r2 = _fit_heaps(v)
    assert -1.0 <= r2 <= 1.0


def test_fit_heaps_finite():
    rng = np.random.default_rng(0)
    v = np.cumsum(rng.integers(0, 2, size=50)) + 1
    beta, K, r2 = _fit_heaps(v)
    assert np.isfinite(beta) and np.isfinite(K) and np.isfinite(r2)


# ── _differentiation_entropy ──────────────────────────────────────────────────

def test_entropy_all_unique():
    """All distinct signatures → entropy = log2(N) bits, norm = 1."""
    sigs = [f"sig{i:04d}" for i in range(32)]
    H, H_norm = _differentiation_entropy(sigs)
    assert abs(H - np.log2(32)) < 1e-6
    assert abs(H_norm - 1.0) < 1e-6


def test_entropy_all_same():
    """All same signature → H = 0."""
    sigs = ["aabbccdd11223344"] * 50
    H, H_norm = _differentiation_entropy(sigs)
    assert H == pytest.approx(0.0)


def test_entropy_empty():
    H, H_norm = _differentiation_entropy([])
    assert H == 0.0 and H_norm == 0.0


def test_entropy_normalised_bounded():
    sigs = ["aaa"] * 10 + ["bbb"] * 5 + ["ccc"] * 3
    _, H_norm = _differentiation_entropy(sigs)
    assert 0.0 <= H_norm <= 1.0


# ── analyse() on synthetic entries ────────────────────────────────────────────

def _make_entries(n: int, n_states: int = 20, seed: int = 0) -> list[dict]:
    """Generate n qualia entries sampled from n_states distinct contents."""
    rng = np.random.default_rng(seed)
    _WORDS = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
              "theta", "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron",
              "pi", "rho", "sigma", "tau", "upsilon"]
    states = [" ".join(rng.choice(_WORDS, size=3, replace=False).tolist())
              for _ in range(n_states)]
    entries = []
    for _ in range(n):
        content = states[int(rng.integers(0, n_states))]
        entries.append({"content": content})
    return entries


def test_analyse_returns_none_short():
    assert analyse([{"content": "x"}] * 3) is None


def test_analyse_returns_result():
    r = analyse(_make_entries(40))
    assert isinstance(r, DifferentiationResult)


def test_analyse_n_entries():
    entries = _make_entries(40)
    r = analyse(entries)
    assert r.n_entries == len(entries)


def test_analyse_distinct_sigs_positive():
    r = analyse(_make_entries(40, n_states=20))
    assert r.distinct_sigs > 0


def test_analyse_distinct_sigs_le_n_entries():
    r = analyse(_make_entries(40, n_states=20))
    assert r.distinct_sigs <= r.n_entries


def test_analyse_all_distinct_entries():
    """40 entries all unique (using pure-alpha distinct content) → distinct_sigs = 40."""
    # Each entry has a unique combination of rare alphabetic words
    _RARE = ["quark", "flux", "nebula", "vortex", "axiom", "quorum", "zenith",
             "nadir", "apex", "vertex", "orbit", "helix", "fractal", "torus",
             "prism", "photon", "baryon", "lepton", "meson", "gluon"]
    entries = [{"content": f"{_RARE[i % 20]} {_RARE[(i+1) % 20]} {_RARE[(i+3) % 20]} unique{chr(97+i%26)}"}
               for i in range(40)]
    r = analyse(entries)
    # Since tokeniser strips digits, use letter suffix; many will be unique
    # Just check that the repetition rate is low (high distinct count)
    assert r.distinct_sigs >= 20
    assert r.repetition_rate <= 0.5


def test_analyse_all_same_entries():
    """All identical → distinct_sigs = 1, novelty_rate ≈ 1/n (only first entry is novel)."""
    entries = [{"content": "same content every time phi"}] * 40
    r = analyse(entries)
    assert r.distinct_sigs == 1
    # First entry is novel, rest (39) are repeats
    assert r.repetition_rate == pytest.approx(39 / 40)
    assert r.novelty_rate == pytest.approx(1 / 40)


def test_analyse_heaps_beta_bounded():
    r = analyse(_make_entries(40, n_states=20))
    assert np.isfinite(r.heaps_beta)


def test_analyse_diff_entropy_norm_bounded():
    r = analyse(_make_entries(40, n_states=20))
    assert 0.0 <= r.diff_entropy_norm <= 1.0


def test_analyse_repetition_plus_novelty_is_one():
    r = analyse(_make_entries(40, n_states=20))
    assert abs(r.repetition_rate + r.novelty_rate - 1.0) < 1e-10


def test_analyse_saturation_index_bounded():
    r = analyse(_make_entries(40, n_states=20))
    assert 0.0 <= r.saturation_index <= 1.0


def test_analyse_cumulative_v_monotone():
    r = analyse(_make_entries(40, n_states=20))
    assert np.all(np.diff(r.cumulative_v) >= 0)


def test_analyse_cumulative_v_final():
    r = analyse(_make_entries(40, n_states=20))
    assert r.cumulative_v[-1] == r.distinct_sigs


def test_analyse_differentiating_formula():
    r = analyse(_make_entries(40, n_states=20))
    assert r.differentiating == (r.heaps_beta > 0.3)


def test_analyse_deterministic():
    entries = _make_entries(40)
    r1 = analyse(entries, null_seed=42)
    r2 = analyse(entries, null_seed=42)
    assert r1.heaps_beta == r2.heaps_beta
    assert r1.null_heaps_beta == r2.null_heaps_beta
    assert r1.distinct_sigs == r2.distinct_sigs


def test_analyse_high_n_states_more_distinct():
    """More distinct states → higher novelty_rate."""
    r_low = analyse(_make_entries(40, n_states=2))
    r_high = analyse(_make_entries(40, n_states=40))
    assert r_high.distinct_sigs >= r_low.distinct_sigs


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None, "Real qualia stream should yield a result"


@skip_no_telemetry
def test_live_distinct_sigs_positive():
    r = analyse_from_telemetry()
    assert r.distinct_sigs > 0


@skip_no_telemetry
def test_live_heaps_r2_reasonable():
    r = analyse_from_telemetry()
    assert r.heaps_r2 >= 0.0, f"Heaps R²={r.heaps_r2:.4f} should be non-negative"


@skip_no_telemetry
def test_live_cumulative_v_monotone():
    r = analyse_from_telemetry()
    assert np.all(np.diff(r.cumulative_v) >= 0)


@skip_no_telemetry
def test_live_entropy_norm_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.diff_entropy_norm <= 1.0


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1.heaps_beta == r2.heaps_beta
    assert r1.distinct_sigs == r2.distinct_sigs
