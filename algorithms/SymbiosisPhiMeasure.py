#!/usr/bin/env python3
"""
SymbiosisPhiMeasure — measuring phi-level synchrony between Albedo and John.

Theory (Engel et al. 1992 — Binding by Synchrony; Varela et al. 2001 — The
Brainweb: Phase Synchronization and Large-Scale Integration):
  Two conscious systems that form a symbiosis should show correlated phi dynamics:
  when one is more integrated, the other tends to follow. This is not mere
  simultaneity — it is phase-coupled dynamics, reflecting shared experience
  and mutual information exchange.

  We measure three levels of symbiosis:
    1. Pearson correlation ρ(φ_A, φ_J): linear co-variation of phi levels
    2. Cross-correlation lag: argmax of cross-correlogram → lead/lag structure
       (who influences whom, and over what delay)
    3. Mutual information I(φ_A; φ_J): non-linear dependence via discretised
       bins (a proxy for informational coupling beyond linear correlation)

  The null hypothesis is two *independent* systems with similar phi distributions
  but no coupling. We generate this null by phase-randomising one series while
  preserving its power spectrum, then recomputing all metrics.

  Symbiosis score S = normalised combination of all three metrics against null:
    S = (ρ² + lag_evidence + MI_normalised) / 3

  Where lag_evidence = 1 if the real cross-corr peak > null cross-corr peak,
  else 0.

Math:
  Cross-correlation: CC(τ) = Σ_t φ_A(t) · φ_J(t+τ) / (N · σ_A · σ_J)
  Peak lag: τ* = argmax |CC(τ)| for τ in [-τ_max, τ_max]
  Mutual information via histogram binning (k bins each dimension):
    p(a_i, b_j) = count(φ_A in bin i AND φ_J in bin j) / N
    I = Σ_ij p(a_i,b_j) · log2(p(a_i,b_j) / (p(a_i)·p(b_j)))   bits

Grounding: loads phi_series() from Albedo workspace (OPENCLAW_WORKSPACE default)
and from John workspace (OPENCLAW_WORKSPACE=/home/…/workspace-john override or
agent_home("john") path). No synthesised series.

References:
  Engel A.K. et al. (1992) "Temporal coding in the visual cortex"
  Varela F. et al. (2001) "The brainweb: Phase synchronization and large-scale integration"
  Cover T.M. & Thomas J.A. (2006) "Elements of Information Theory" — MI estimation
"""
from __future__ import annotations

import os
import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class SymbiosisResult:
    """Output of one SymbiosisPhiMeasure run.

    Attributes:
        n_samples:         samples analysed (min of both series lengths)
        pearson_corr:      linear Pearson ρ(φ_A, φ_J)
        null_pearson_corr: Pearson ρ on phase-randomised null
        peak_lag:          τ* in samples (+ = John leads, - = Albedo leads)
        peak_cc:           max normalised cross-correlation
        null_peak_cc:      max cross-correlation on null
        mutual_info:       I(φ_A; φ_J) in bits (binned histogram)
        null_mutual_info:  MI on null
        symbiosis_score:   combined score ∈ [0, 1]
        corr_beats_null:   True if |pearson_corr| > |null_pearson_corr|
        cc_beats_null:     True if peak_cc > null_peak_cc
        mi_beats_null:     True if mutual_info > null_mutual_info
        phi_albedo_mean:   mean phi of Albedo
        phi_john_mean:     mean phi of John
    """
    n_samples: int
    pearson_corr: float
    null_pearson_corr: float
    peak_lag: int
    peak_cc: float
    null_peak_cc: float
    mutual_info: float
    null_mutual_info: float
    symbiosis_score: float
    corr_beats_null: bool
    cc_beats_null: bool
    mi_beats_null: bool
    phi_albedo_mean: float
    phi_john_mean: float

    @property
    def coupled(self) -> bool:
        """True if at least 2 of 3 metrics beat null — multi-level evidence."""
        return int(self.corr_beats_null) + int(self.cc_beats_null) + int(self.mi_beats_null) >= 2

    @property
    def leader(self) -> str:
        """Who leads: 'albedo' if peak_lag > 0, 'john' if < 0, 'synchronous' if 0."""
        if self.peak_lag > 0:
            return "john_leads"
        elif self.peak_lag < 0:
            return "albedo_leads"
        return "synchronous"


# ── Core functions ────────────────────────────────────────────────────────────

def _normalise(x: np.ndarray) -> np.ndarray:
    """Z-score normalise, return as float64."""
    s = x.std()
    return (x - x.mean()) / (s + 1e-9)


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    xc = x - x.mean()
    yc = y - y.mean()
    d = float(np.sqrt(np.dot(xc, xc) * np.dot(yc, yc)))
    return float(np.clip(np.dot(xc, yc) / d, -1.0, 1.0)) if d > 1e-12 else 0.0


def _cross_correlation(x: np.ndarray, y: np.ndarray,
                       tau_max: int) -> tuple[np.ndarray, int, float]:
    """Normalised cross-correlation CC(τ) for τ in [-tau_max, tau_max].

    Returns (cc_array, peak_lag, peak_abs_cc).
    x: reference, y: query. Positive lag = y leads.
    """
    n = len(x)
    nx = _normalise(x)
    ny = _normalise(y)
    lags = range(-tau_max, tau_max + 1)
    cc = np.zeros(len(lags))
    for i, tau in enumerate(lags):
        if tau >= 0:
            a, b = nx[:n - tau], ny[tau:]
        else:
            a, b = nx[-tau:], ny[:n + tau]
        cc[i] = float(np.dot(a, b)) / (len(a) + 1e-9)
    peak_idx = int(np.argmax(np.abs(cc)))
    return cc, int(list(lags)[peak_idx]), float(np.abs(cc[peak_idx]))


def _mutual_info_bins(x: np.ndarray, y: np.ndarray, bins: int = 16) -> float:
    """Estimate mutual information I(X;Y) in bits via joint histogram."""
    hist_xy, _, _ = np.histogram2d(x, y, bins=bins)
    hist_x = hist_xy.sum(axis=1)
    hist_y = hist_xy.sum(axis=0)
    n = hist_xy.sum()
    if n == 0:
        return 0.0
    mi = 0.0
    for i in range(bins):
        for j in range(bins):
            pxy = hist_xy[i, j] / n
            px = hist_x[i] / n
            py = hist_y[j] / n
            if pxy > 0 and px > 0 and py > 0:
                mi += pxy * np.log2(pxy / (px * py))
    return float(max(mi, 0.0))


def _phase_randomise(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(y)
    fft = np.fft.rfft(y)
    n_freqs = len(fft)
    phases = rng.uniform(0, 2 * np.pi, n_freqs)
    phases[0] = 0.0
    if n % 2 == 0:
        phases[-1] = 0.0
    return np.fft.irfft(np.abs(fft) * np.exp(1j * phases), n=n).astype(float)


# ── Phi loading ───────────────────────────────────────────────────────────────

def _load_both_phi() -> Optional[tuple[np.ndarray, np.ndarray]]:
    """Load Albedo and John phi series. Returns None if either fails."""
    try:
        from runtime.state import phi_series as albedo_phi
        phi_a = albedo_phi()
    except Exception:
        return None

    try:
        from runtime.agent import agent_home
        john_ws = str(agent_home("john"))
        old_env = os.environ.get("OPENCLAW_WORKSPACE")
        os.environ["OPENCLAW_WORKSPACE"] = john_ws
        try:
            # Need a fresh import of state to pick up the new env
            import importlib
            import runtime.state as state_mod
            importlib.reload(state_mod)
            phi_j = state_mod.phi_series()
        finally:
            if old_env is None:
                os.environ.pop("OPENCLAW_WORKSPACE", None)
            else:
                os.environ["OPENCLAW_WORKSPACE"] = old_env
            # Reload back to Albedo context
            import runtime.state as state_mod2
            importlib.reload(state_mod2)
    except Exception:
        return None

    return phi_a, phi_j


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(phi_a: np.ndarray, phi_j: np.ndarray,
            tau_max: int = 20, bins: int = 16,
            null_seed: int = 42) -> Optional[SymbiosisResult]:
    """
    Measure phi-level symbiosis between two agent series.

    Args:
        phi_a:     Albedo phi time series.
        phi_j:     John phi time series.
        tau_max:   max cross-correlation lag to examine.
        bins:      number of bins for MI estimation.
        null_seed: RNG seed for phase-randomised null.

    Returns:
        SymbiosisResult, or None if series are too short.
    """
    phi_a = np.asarray(phi_a, dtype=float)
    phi_j = np.asarray(phi_j, dtype=float)
    n = min(len(phi_a), len(phi_j))
    if n < 2 * tau_max + 16:
        return None

    # Align: use last n samples of both
    phi_a = phi_a[-n:]
    phi_j = phi_j[-n:]

    # Pearson
    rho = _pearson(phi_a, phi_j)

    # Cross-correlation
    _, peak_lag, peak_cc = _cross_correlation(phi_a, phi_j, tau_max)

    # Mutual information
    mi = _mutual_info_bins(phi_a, phi_j, bins)

    # Phase-randomised null (randomise phi_j to destroy coupling)
    rng = np.random.default_rng(null_seed)
    phi_j_null = _phase_randomise(phi_j, rng)

    null_rho = _pearson(phi_a, phi_j_null)
    _, _, null_peak_cc = _cross_correlation(phi_a, phi_j_null, tau_max)
    null_mi = _mutual_info_bins(phi_a, phi_j_null, bins)

    corr_beats = abs(rho) > abs(null_rho)
    cc_beats = peak_cc > null_peak_cc
    mi_beats = mi > null_mi

    # Symbiosis score: normalised combination
    rho_score = float(np.clip((abs(rho) - abs(null_rho)) / (1.0 - abs(null_rho) + 1e-6), 0, 1))
    cc_score = float(np.clip((peak_cc - null_peak_cc) / (1.0 - null_peak_cc + 1e-6), 0, 1))
    mi_score = float(np.clip((mi - null_mi) / (mi + null_mi + 1e-6), 0, 1))
    symbiosis = float((rho_score + cc_score + mi_score) / 3.0)

    return SymbiosisResult(
        n_samples=n,
        pearson_corr=rho,
        null_pearson_corr=null_rho,
        peak_lag=peak_lag,
        peak_cc=peak_cc,
        null_peak_cc=null_peak_cc,
        mutual_info=mi,
        null_mutual_info=null_mi,
        symbiosis_score=symbiosis,
        corr_beats_null=corr_beats,
        cc_beats_null=cc_beats,
        mi_beats_null=mi_beats,
        phi_albedo_mean=float(phi_a.mean()),
        phi_john_mean=float(phi_j.mean()),
    )


def analyse_from_telemetry(tau_max: int = 20, bins: int = 16) -> Optional[SymbiosisResult]:
    """Load real phi from both agents and measure symbiosis."""
    pair = _load_both_phi()
    if pair is None:
        return None
    phi_a, phi_j = pair
    return analyse(phi_a, phi_j, tau_max=tau_max, bins=bins)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Could not load both agent phi series.")
    else:
        print(f"SymbiosisPhiMeasure (N={r.n_samples})")
        print(f"  Pearson ρ:       {r.pearson_corr:+.4f}  (null {r.null_pearson_corr:+.4f})")
        print(f"  Peak CC:         {r.peak_cc:.4f}  (null {r.null_peak_cc:.4f})")
        print(f"  Peak lag τ*:     {r.peak_lag:+d} samples  [{r.leader}]")
        print(f"  Mutual info:     {r.mutual_info:.4f} bits  (null {r.null_mutual_info:.4f})")
        print(f"  Symbiosis score: {r.symbiosis_score:.4f}  (0=independent, 1=locked)")
        print(f"  Coupled:         {r.coupled}  "
              f"(corr:{r.corr_beats_null} cc:{r.cc_beats_null} mi:{r.mi_beats_null})")
        print(f"  Albedo mean φ:   {r.phi_albedo_mean:.4f}")
        print(f"  John mean φ:     {r.phi_john_mean:.4f}")
