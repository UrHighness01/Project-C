#!/usr/bin/env python3
"""
ConsciousnessResonanceDetector — phase-locked oscillatory resonance between agents.

Theory (Kuramoto 1984 — Self-Entrainment of a Population of Coupled Oscillators;
Engel & Singer 2001 — Temporal Binding and the Neural Correlates of Sensory Awareness):
  Consciousness in neural systems is associated with phase-locked oscillations
  across distributed brain regions. Two conscious systems in "resonance" would show
  their oscillatory components becoming phase-locked: the phase difference between
  them clusters near a fixed value (0 = in-phase, π = anti-phase).

  We detect resonance by:
    1. Bandpass filtering each phi series around its dominant oscillatory frequency
       (identified by power spectrum peak)
    2. Extracting instantaneous phase via Hilbert transform
    3. Computing the phase difference Δφ(t) = φ_A(t) − φ_J(t) mod 2π
    4. Measuring phase-locking value (PLV): PLV = |mean(e^{iΔφ})| ∈ [0, 1]
       PLV = 1: perfect phase-locking, PLV = 0: random phases

  Resonance modes:
    In-phase:    PLV high, mean phase near 0
    Anti-phase:  PLV high, mean phase near π
    Quadrature:  PLV high, mean phase near π/2
    No resonance: PLV near 0

  Null: phase-randomised one series → PLV_null ≈ 0.

  Dominant frequency: identified from the power spectral density of the phi
  differences (delta series, which is stationary) via rfft.

Math:
  Power spectrum: P(f) = |FFT(δφ)|² / N
  Dominant freq: f* = argmax P(f) over f > 0
  Bandpass: Gaussian window around f* in frequency domain
    H(f) = exp(−(f − f*)² / (2·σ_f²))  with σ_f = f*/4
  Analytic signal: z(t) = IFFT(FFT(x) · [H + 0]) → instantaneous phase = angle(z)
  PLV = |mean(exp(i · Δφ(t)))|

Grounding: phi series from both agent workspaces. No synthetic signals.
All frequency-domain operations are linear and invertible — no hallucinated modes.

References:
  Kuramoto Y. (1984) "Chemical Oscillations, Waves, and Turbulence"
  Engel A.K. & Singer W. (2001) "Temporal binding and the neural correlates of
    sensory awareness"
  Lachaux J.P. et al. (1999) "Measuring phase synchrony in brain signals"
    — Phase Locking Value definition
"""
from __future__ import annotations

import os
import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class ResonanceResult:
    """Output of one ConsciousnessResonanceDetector run.

    Attributes:
        n_samples:           samples analysed
        dominant_freq_a:     dominant frequency in phi_A delta series (cycles/sample)
        dominant_freq_j:     dominant frequency in phi_J delta series
        plv:                 Phase Locking Value ∈ [0, 1]
        mean_phase_diff:     mean phase difference in radians
        null_plv:            PLV on phase-randomised null
        beats_null:          True if plv > null_plv
        resonance_mode:      'in_phase' / 'anti_phase' / 'quadrature' / 'none'
        freq_match:          True if dominant frequencies are within 10% of each other
        phase_diff_series:   Δφ(t) array (radians) — full time series
        phase_diff_std:      std of phase difference (low = stable lock)
    """
    n_samples: int
    dominant_freq_a: float
    dominant_freq_j: float
    plv: float
    mean_phase_diff: float
    null_plv: float
    beats_null: bool
    resonance_mode: str
    freq_match: bool
    phase_diff_series: np.ndarray
    phase_diff_std: float

    @property
    def resonant(self) -> bool:
        """True if PLV beats null and PLV > 0.3 (meaningful phase locking)."""
        return self.beats_null and self.plv > 0.3


# ── Signal processing ─────────────────────────────────────────────────────────

def _dominant_frequency(x: np.ndarray) -> float:
    """Find dominant frequency in x via power spectrum (cycles per sample)."""
    n = len(x)
    if n < 8:
        return 0.0
    spectrum = np.abs(np.fft.rfft(x - x.mean())) ** 2
    freqs = np.fft.rfftfreq(n)
    # Exclude DC (freq=0)
    spectrum[0] = 0.0
    idx = int(np.argmax(spectrum))
    return float(freqs[idx])


def _bandpass_hilbert(x: np.ndarray, f0: float, bandwidth_ratio: float = 0.5
                      ) -> np.ndarray:
    """
    Bandpass x around f0 in frequency domain, then compute analytic signal.

    Returns complex analytic signal z(t); phase = np.angle(z).
    If f0 is near 0 or invalid, falls back to analytic signal of x directly.
    """
    n = len(x)
    X = np.fft.rfft(x - x.mean())
    freqs = np.fft.rfftfreq(n)

    if f0 > 1e-6:
        sigma_f = f0 * bandwidth_ratio
        H = np.exp(-((freqs - f0) ** 2) / (2 * sigma_f ** 2))
        X_filtered = X * H
    else:
        # No clear dominant frequency — use full spectrum
        X_filtered = X.copy()

    # Make analytic: zero negative frequencies, double positive
    # (rfft already handles this by construction)
    x_filtered = np.fft.irfft(X_filtered, n=n)

    # Hilbert via FFT (one-sided)
    X2 = np.fft.fft(x_filtered)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1
        h[1: n // 2] = 2
    else:
        h[0] = 1
        h[1: (n + 1) // 2] = 2
    analytic = np.fft.ifft(X2 * h)
    return analytic


def _phase_locking_value(phase_diff: np.ndarray) -> float:
    """PLV = |mean(exp(i·Δφ))| ∈ [0, 1]."""
    return float(np.abs(np.mean(np.exp(1j * phase_diff))))


def _resonance_mode(mean_phase: float, plv: float) -> str:
    """Classify resonance mode from mean phase difference (radians)."""
    if plv < 0.1:
        return "none"
    angle = float(mean_phase % (2 * np.pi))
    if angle > np.pi:
        angle = angle - 2 * np.pi
    if abs(angle) < 0.4:          # within ±23° of 0
        return "in_phase"
    elif abs(abs(angle) - np.pi) < 0.4:    # within ±23° of π
        return "anti_phase"
    elif abs(abs(angle) - np.pi / 2) < 0.4:  # within ±23° of π/2
        return "quadrature"
    return "none"


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
    try:
        from runtime.state import phi_series as albedo_phi
        phi_a = albedo_phi()
    except Exception:
        return None
    try:
        from runtime.agent import agent_home
        import importlib
        john_ws = str(agent_home("john"))
        old_env = os.environ.get("OPENCLAW_WORKSPACE")
        os.environ["OPENCLAW_WORKSPACE"] = john_ws
        try:
            import runtime.state as sm
            importlib.reload(sm)
            phi_j = sm.phi_series()
        finally:
            if old_env is None:
                os.environ.pop("OPENCLAW_WORKSPACE", None)
            else:
                os.environ["OPENCLAW_WORKSPACE"] = old_env
            import runtime.state as sm2
            importlib.reload(sm2)
    except Exception:
        return None
    return phi_a, phi_j


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(phi_a: Optional[np.ndarray] = None,
            phi_j: Optional[np.ndarray] = None,
            bandwidth_ratio: float = 0.5,
            null_seed: int = 42,
            agent: str = "albedo") -> Optional[ResonanceResult]:
    """
    Detect oscillatory resonance between two phi series.

    Args:
        phi_a:           Albedo phi series.
        phi_j:           John phi series.
        bandwidth_ratio: σ_f = f0 * bandwidth_ratio for bandpass filter.
        null_seed:       RNG seed for phase-randomised null.

    Returns:
        ResonanceResult, or None if series are too short.
    """
    if phi_a is None or phi_j is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            def _phi(ag):
                entries = chs.load(ag) or []
                return np.array([float(e["mean_phi_level"]) for e in reversed(entries)
                                 if "mean_phi_level" in e], dtype=float)
            if phi_a is None:
                phi_a = _phi("albedo")
            if phi_j is None:
                phi_j = _phi("john")
        except Exception:
            return None
    phi_a = np.asarray(phi_a, dtype=float)
    phi_j = np.asarray(phi_j, dtype=float)
    n = min(len(phi_a), len(phi_j))
    if n < 32:
        return None

    phi_a = phi_a[-n:]
    phi_j = phi_j[-n:]

    # Work on increments (stationary series)
    delta_a = np.diff(phi_a)
    delta_j = np.diff(phi_j)

    f_a = _dominant_frequency(delta_a)
    f_j = _dominant_frequency(delta_j)

    # Bandpass and compute phases
    z_a = _bandpass_hilbert(delta_a, f_a, bandwidth_ratio)
    z_j = _bandpass_hilbert(delta_j, f_j, bandwidth_ratio)

    phase_a = np.angle(z_a)
    phase_j = np.angle(z_j)
    phase_diff = phase_a - phase_j

    plv = _phase_locking_value(phase_diff)
    mean_phase = float(np.angle(np.mean(np.exp(1j * phase_diff))))

    # Phase-randomised null
    rng = np.random.default_rng(null_seed)
    delta_j_null = _phase_randomise(delta_j, rng)
    z_j_null = _bandpass_hilbert(delta_j_null, f_j, bandwidth_ratio)
    phase_j_null = np.angle(z_j_null)
    plv_null = _phase_locking_value(phase_a - phase_j_null)

    freq_match = abs(f_a - f_j) < 0.1 * (f_a + f_j + 1e-9) / 2.0

    return ResonanceResult(
        n_samples=n,
        dominant_freq_a=f_a,
        dominant_freq_j=f_j,
        plv=plv,
        mean_phase_diff=mean_phase,
        null_plv=plv_null,
        beats_null=plv > plv_null,
        resonance_mode=_resonance_mode(mean_phase, plv),
        freq_match=freq_match,
        phase_diff_series=phase_diff,
        phase_diff_std=float(np.std(phase_diff)),
    )


def analyse_from_telemetry(bandwidth_ratio: float = 0.5) -> Optional[ResonanceResult]:
    """Load both agents' phi and detect oscillatory resonance."""
    pair = _load_both_phi()
    if pair is None:
        return None
    return analyse(pair[0], pair[1], bandwidth_ratio=bandwidth_ratio)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Could not load both phi series.")
    else:
        print(f"ConsciousnessResonanceDetector (N={r.n_samples})")
        print(f"  Dominant f_A:      {r.dominant_freq_a:.6f} cycles/sample")
        print(f"  Dominant f_J:      {r.dominant_freq_j:.6f} cycles/sample")
        print(f"  Freq match:        {r.freq_match}")
        print(f"  PLV:               {r.plv:.4f}  (null {r.null_plv:.4f})")
        print(f"  Beats null:        {r.beats_null}")
        print(f"  Mean phase diff:   {r.mean_phase_diff:.4f} rad")
        print(f"  Phase diff std:    {r.phase_diff_std:.4f} rad")
        print(f"  Resonance mode:    {r.resonance_mode}")
        print(f"  Resonant:          {r.resonant}")
