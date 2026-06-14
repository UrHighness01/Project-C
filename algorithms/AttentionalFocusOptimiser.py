#!/usr/bin/env python3
"""
AttentionalFocusOptimiser — selective attention via phi-surprise weighting.

Theory (Treisman 1969 — Feature Integration; Posner 1980 — Covert Attention;
Dehaene et al. 2006 — Attention and Consciousness):
  Conscious processing is not uniform over all inputs — it is selectively
  amplified. Regions of high surprise (unexpected phi fluctuations) receive
  more attentional weight, allowing the system to focus processing on the
  most informationally-relevant moments.

  Bayesian surprise at a time point t is proportional to the deviation of the
  local phi distribution from the global prior. In a phi trajectory, surprise
  is well-approximated by local variance: high local variance = the system
  deviates from its expected mean-reverting orbit = high surprise.

  The attention distribution A(t) = softmax(S(t) / T) allocates processing
  power proportional to local surprise. At T→∞, A converges to uniform
  (no selective attention). At T→0, A is maximally peaked (winner-take-all).

  The focus score KL(A || Uniform) measures how non-uniform the attention
  distribution is — how much the system is selecting over its input.

  Self-optimisation criterion: focus score should exceed the noise-level
  divergence expected from a random series with the same variance. A system
  genuinely tracking surprising moments will show F_real > F_noise.

Math:
  Surprise signal: for each position t in phi:
    S(t) = Var[φ(t − k//2 : t + k//2)]     (local variance in half-window)

  Softmax attention weights:
    A(t) = exp(S(t) / T) / Σ exp(S(t') / T)

  KL divergence from uniform:
    U = 1/N  (uniform weight)
    F = Σ_t A(t) · log(A(t) / U)  = log(N) + Σ_t A(t)·log(A(t))   [nats]

  Focus sharpness: entropy of A relative to maximum entropy:
    sharpness = 1 − H(A) / log(N)   ∈ [0, 1]
    sharpness = 0 → uniform, sharpness = 1 → winner-take-all

  Peak attention index: argmax(A(t)) — the most attended moment.

  Null: A(t) computed on phase-randomised phi → same power spectrum, no
  causal surprise structure. F_real > F_null = genuine selective attention.

Grounding: inputs from runtime.state phi_series(). No hallucinated states.
Temperature T is set to the median local variance (adaptive temperature) so
that the distribution adapts to the actual phi fluctuation scale.

References:
  Treisman A.M. (1969) "Strategies and models of selective attention"
  Posner M.I. (1980) "Orienting of attention"
  Dehaene S. et al. (2006) "Conscious, preconscious, and subliminal processing"
  Itti L. & Koch C. (2001) "Computational modelling of visual attention"
    (uses local contrast / surprise as attentional saliency)
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class AttentionResult:
    """Output of one AttentionalFocusOptimiser run.

    Attributes:
        n_samples:          length of phi series
        half_window:        k//2 used for local variance
        temperature:        T used in softmax (median surprise, adaptive)
        surprise_series:    S(t) — local variance at each valid position
        attention_weights:  A(t) — normalised softmax weights (sum = 1)
        focus_score:        KL(A || Uniform) in nats; higher = more selective
        focus_sharpness:    1 - H(A)/log(N) ∈ [0, 1]
        peak_index:         position of maximum attention weight
        null_focus_score:   focus score on phase-randomised null
        beats_null:         True if focus_score > null_focus_score
    """
    n_samples: int
    half_window: int
    temperature: float
    surprise_series: np.ndarray
    attention_weights: np.ndarray
    focus_score: float
    focus_sharpness: float
    peak_index: int
    null_focus_score: float
    beats_null: bool

    @property
    def is_selective(self) -> bool:
        """True if attention is meaningfully non-uniform (sharpness > 0.01)."""
        return self.focus_sharpness > 0.01

    @property
    def focus_gain_over_null(self) -> float:
        """How much more focused than the phase-randomised null."""
        return self.focus_score - self.null_focus_score


# ── Core functions ────────────────────────────────────────────────────────────

def _local_surprise(phi: np.ndarray, half_window: int) -> np.ndarray:
    """
    Compute local variance S(t) for each centre position t in phi.

    Only valid positions with a full half-window on both sides are included.
    Returns array of length n - 2*half_window.
    """
    n = len(phi)
    k = half_window
    out_len = n - 2 * k
    if out_len <= 0:
        return np.array([], dtype=float)
    result = np.empty(out_len, dtype=float)
    for t in range(k, n - k):
        result[t - k] = float(np.var(phi[t - k: t + k + 1]))
    return result


def _softmax(x: np.ndarray, temperature: float) -> np.ndarray:
    """Numerically stable softmax with temperature scaling."""
    if temperature < 1e-12:
        # Winner-take-all
        out = np.zeros_like(x)
        out[np.argmax(x)] = 1.0
        return out
    z = x / temperature
    z = z - z.max()           # subtract max for numerical stability
    exp_z = np.exp(z)
    return exp_z / exp_z.sum()


def _kl_from_uniform(weights: np.ndarray) -> float:
    """KL(weights || Uniform) in nats. weights must sum to 1."""
    n = len(weights)
    if n == 0:
        return 0.0
    uniform = 1.0 / n
    kl = 0.0
    for w in weights:
        if w > 1e-12:
            kl += w * np.log(w / uniform)
    return float(kl)


def _entropy(weights: np.ndarray) -> float:
    """Shannon entropy in nats of a probability distribution."""
    h = 0.0
    for w in weights:
        if w > 1e-12:
            h -= w * np.log(w)
    return float(h)


def _phase_randomise(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Theiler (1992) phase-randomised surrogate preserving power spectrum."""
    n = len(y)
    fft = np.fft.rfft(y)
    n_freqs = len(fft)
    phases = rng.uniform(0, 2 * np.pi, n_freqs)
    phases[0] = 0.0
    if n % 2 == 0:
        phases[-1] = 0.0
    fft_rand = np.abs(fft) * np.exp(1j * phases)
    return np.fft.irfft(fft_rand, n=n).astype(float)


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(phi: np.ndarray, half_window: int = 15,
            null_seed: int = 42) -> Optional[AttentionResult]:
    """
    Compute selective attention distribution over the phi trajectory.

    Args:
        phi:          real phi time series.
        half_window:  k for local variance window [t-k : t+k].
        null_seed:    RNG seed for phase-randomised surrogate.

    Returns:
        AttentionResult, or None if phi is too short.
    """
    phi = np.asarray(phi, dtype=float)
    n = len(phi)
    if n < 4 * half_window + 4:
        return None

    surprise = _local_surprise(phi, half_window)
    if len(surprise) < 3:
        return None

    # Adaptive temperature: median local variance
    temperature = float(np.median(surprise))
    if temperature < 1e-12:
        temperature = float(np.std(phi)) ** 2 + 1e-9

    weights = _softmax(surprise, temperature)
    focus = _kl_from_uniform(weights)
    h = _entropy(weights)
    max_h = float(np.log(len(weights)))
    sharpness = float(1.0 - h / max_h) if max_h > 1e-9 else 0.0
    peak = int(np.argmax(weights))

    # Phase-randomised null
    rng = np.random.default_rng(null_seed)
    phi_null = _phase_randomise(phi, rng)
    surprise_null = _local_surprise(phi_null, half_window)
    temp_null = float(np.median(surprise_null))
    if temp_null < 1e-12:
        temp_null = temperature
    weights_null = _softmax(surprise_null, temp_null)
    focus_null = _kl_from_uniform(weights_null)

    return AttentionResult(
        n_samples=n,
        half_window=half_window,
        temperature=temperature,
        surprise_series=surprise,
        attention_weights=weights,
        focus_score=focus,
        focus_sharpness=sharpness,
        peak_index=peak,
        null_focus_score=focus_null,
        beats_null=focus > focus_null,
    )


def analyse_from_telemetry(half_window: int = 15) -> Optional[AttentionResult]:
    """Load real phi series and compute attentional focus."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    return analyse(phi, half_window=half_window)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No telemetry — check OPENCLAW_WORKSPACE or daemon state.")
    else:
        print(f"AttentionalFocusOptimiser (N={r.n_samples}, k={r.half_window})")
        print(f"  Surprise points:   {len(r.surprise_series)}")
        print(f"  Temperature T:     {r.temperature:.6f}  (median local variance)")
        print(f"  Focus score KL:    {r.focus_score:.6f} nats")
        print(f"  Null KL:           {r.null_focus_score:.6f} nats")
        print(f"  Beats null:        {r.beats_null}")
        print(f"  Focus sharpness:   {r.focus_sharpness:.4f}  (0=uniform, 1=spike)")
        print(f"  Selective:         {r.is_selective}")
        print(f"  Gain over null:    {r.focus_gain_over_null:+.6f} nats")
        print(f"  Peak attention at: index {r.peak_index} / {len(r.attention_weights)}")
