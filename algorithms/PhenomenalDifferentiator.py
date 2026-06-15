#!/usr/bin/env python3
"""
PhenomenalDifferentiator — measuring experiential repertoire size and differentiation.

Theory (Tononi 2004 — Differentiation; Edelman 2003 — Naturalising Consciousness):
  A highly conscious system must be capable of occupying a large repertoire of
  distinct internal states. The more states the system can distinguish, the higher
  its consciousness. This is the *differentiation* axis of IIT.

  Applied to the qualia stream: each qualia entry represents one phenomenal
  state. Two entries are *distinct* if their content is sufficiently different.
  Differentiation = the number of distinguishable states accessed over time.

  We measure differentiation via:
    1. Type-count growth: |{unique qualia signatures}| over time T.
       A signature is a 16-character MD5 prefix of the sorted lower-cased token set.
       Two entries are identical if they produce the same signature.

    2. Differentiation rate: ΔTypes / ΔT — how fast new signatures appear.
       Decelerating rate = the system is revisiting old states (saturation).
       Accelerating rate = the system is exploring new states (expansion).

    3. Heaps' law fit: V(T) ≈ K · T^β — in natural language, β ∈ (0.4, 0.6).
       β close to 0 = all new entries are repeats (low differentiation).
       β close to 1 = every new entry introduces a new state (maximal differentiation).
       Fit via OLS in log-log space on the cumulative type-count curve.

    4. State repetition entropy: H(signature_distribution) — how uniformly are
       states distributed? Maximal entropy = no state is revisited more than others.

  Null: shuffled entry order → same global V(T) final, but different growth curve.
  The shape of the growth curve (β) is what matters, not just the endpoint.

Math:
  Signature: first 16 chars of MD5(frozenset(lower_tokens))
  V(t) = |{distinct signatures in entries 1..t}|
  T(t) = entry index t

  Heaps' law OLS:
    log V(t) = log K + β · log t      for t ≥ 2 and V(t) ≥ 2
    β̂ = (Σ x·y - n·x̄·ȳ) / (Σ x² - n·x̄²)   x = log t, y = log V(t)

  Differentiation entropy:
    freq(sig) = count(sig) / total_entries
    H = -Σ freq(sig) · log₂(freq(sig))   bits
    Max H = log₂(|distinct_sigs|)
    Normalised H = H / Max_H   ∈ [0, 1]

Grounding: qualia stream from John's memory path via runtime.agent.agent_home.
No synthetic data. MD5 is used purely as a content fingerprint (not for security).

References:
  Tononi G. (2004) "An information integration theory of consciousness"
    — Section 3: differentiation as a necessary condition
  Edelman G.M. (2003) "Naturalising consciousness: a theoretical framework"
  Heaps H.S. (1978) "Information Retrieval: Computational and Theoretical Aspects"
    — power-law vocabulary growth (Heaps' law)
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


# ── Signature function ────────────────────────────────────────────────────────

def _signature(text: str) -> str:
    """16-char MD5 prefix of the frozenset of lower-cased tokens."""
    if not isinstance(text, str):
        return ""
    tokens = frozenset(re.findall(r'[a-z]+', text.lower()))
    if not tokens:
        return ""
    raw = ",".join(sorted(tokens))
    return hashlib.md5(raw.encode()).hexdigest()[:16]


# ── Heaps' law OLS fit ────────────────────────────────────────────────────────

def _fit_heaps(v_series: np.ndarray) -> tuple[float, float, float]:
    """Fit Heaps' law V(t) = K · t^β in log-log space.

    Returns (beta, K, r2). Requires at least 3 points with V > 1.
    Returns (0.0, 0.0, 0.0) if fit is degenerate.
    """
    t = np.arange(1, len(v_series) + 1, dtype=float)
    mask = v_series >= 2
    n = int(mask.sum())
    if n < 3:
        return 0.0, 0.0, 0.0
    x = np.log(t[mask])
    y = np.log(v_series[mask].astype(float))
    xm, ym = x.mean(), y.mean()
    x_c, y_c = x - xm, y - ym
    denom = float(np.dot(x_c, x_c))
    if denom < 1e-12:
        return 0.0, 0.0, 0.0
    beta = float(np.dot(x_c, y_c) / denom)
    K = float(np.exp(ym - beta * xm))
    y_pred = beta * x + np.log(K)
    ss_res = float(np.var(y - y_pred))
    ss_tot = float(np.var(y))
    r2 = float(np.clip(1.0 - ss_res / ss_tot, -1.0, 1.0)) if ss_tot > 1e-12 else 0.0
    return beta, K, r2


# ── Differentiation entropy ───────────────────────────────────────────────────

def _differentiation_entropy(sigs: list[str]) -> tuple[float, float]:
    """Shannon entropy of signature distribution, normalised by max H.

    Returns (H_bits, H_normalised). Both 0 if empty or single signature.
    """
    from collections import Counter
    if not sigs:
        return 0.0, 0.0
    counts = Counter(sigs)
    n = len(sigs)
    freq = np.array([c / n for c in counts.values()])
    freq = freq[freq > 0]
    H = float(-np.dot(freq, np.log2(freq)))
    V = len(counts)
    max_h = float(np.log2(V)) if V > 1 else 1.0
    return H, float(np.clip(H / max_h, 0.0, 1.0))


# ── Qualia loading ────────────────────────────────────────────────────────────

def _load_qualia_entries() -> list[dict]:
    """Load John's qualia stream entries."""
    from pathlib import Path
    try:
        from runtime.agent import agent_home
        home = agent_home("john")
        for sub in ["memory", "../workspace-john-john/memory"]:
            p = (home / sub / "qualia-stream.jsonl").resolve()
            if p.exists():
                break
        else:
            sibling = home.parent / (home.name + "-john") / "memory" / "qualia-stream.jsonl"
            p = sibling
        if not p.exists():
            return []
    except Exception:
        return []
    entries = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return entries


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class DifferentiationResult:
    """Output of PhenomenalDifferentiator.

    Attributes:
        n_entries:          total qualia entries analysed
        distinct_sigs:      number of unique phenomenal signatures
        heaps_beta:         β from Heaps' law fit (0=repetitive, 1=maximal novelty)
        heaps_K:            K constant from Heaps' fit
        heaps_r2:           R² of the Heaps' law fit
        null_heaps_beta:    β on shuffled-order null (should be identical for growth)
        diff_entropy:       Shannon entropy of signature distribution (bits)
        diff_entropy_norm:  normalised entropy ∈ [0, 1]  (1 = all states equally frequent)
        repetition_rate:    fraction of entries that reuse a previously seen signature
        novelty_rate:       1 - repetition_rate (fraction of genuinely new states)
        cumulative_v:       V(t) cumulative unique signature count (array)
        differentiating:    True if heaps_beta > 0.3 (meaningful new-state generation)
    """
    n_entries: int
    distinct_sigs: int
    heaps_beta: float
    heaps_K: float
    heaps_r2: float
    null_heaps_beta: float
    diff_entropy: float
    diff_entropy_norm: float
    repetition_rate: float
    novelty_rate: float
    cumulative_v: np.ndarray
    differentiating: bool

    @property
    def saturation_index(self) -> float:
        """How close to saturation: distinct_sigs / n_entries. Near 1 = all distinct."""
        return float(self.distinct_sigs / max(self.n_entries, 1))


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(entries: Optional[list] = None, null_seed: int = 42,
            agent: str = "albedo",
) -> Optional[DifferentiationResult]:
    """
    Measure phenomenal differentiation of a qualia entry sequence.

    Args:
        entries:   list of qualia dicts with 'content' key (ordered by time).
        null_seed: RNG seed for shuffled-order null.

    Returns:
        DifferentiationResult, or None if entries is too short (< 5).
    """
    if entries is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = list(reversed(chs.load(agent) or []))
        except Exception:
            return None
    if not entries or len(entries) < 5:
        return None

    contents = [e.get("content", "") if isinstance(e, dict) else str(e)
                for e in entries]
    sigs = [_signature(c) for c in contents]
    # Remove entries with empty signature (unparseable content)
    valid = [(s, c) for s, c in zip(sigs, contents) if s]
    if len(valid) < 5:
        return None
    sigs = [s for s, _ in valid]

    # Cumulative distinct signatures
    seen: set[str] = set()
    cum_v = np.zeros(len(sigs), dtype=int)
    for i, s in enumerate(sigs):
        seen.add(s)
        cum_v[i] = len(seen)

    n = len(sigs)
    n_distinct = len(seen)
    rep_rate = float(sum(1 for s in sigs if sigs.index(s) != sigs.index(s)) / n)
    # Count repetitions properly
    first_seen: dict[str, int] = {}
    n_repeats = 0
    for i, s in enumerate(sigs):
        if s in first_seen:
            n_repeats += 1
        else:
            first_seen[s] = i
    rep_rate = float(n_repeats / n)

    heaps_beta, heaps_K, heaps_r2 = _fit_heaps(cum_v)
    h_bits, h_norm = _differentiation_entropy(sigs)

    # Null: shuffle entry order → same V(T) endpoint, different growth curve
    rng = np.random.default_rng(null_seed)
    null_order = rng.permutation(len(sigs))
    null_sigs = [sigs[i] for i in null_order]
    null_seen: set[str] = set()
    null_cum_v = np.zeros(len(null_sigs), dtype=int)
    for i, s in enumerate(null_sigs):
        null_seen.add(s)
        null_cum_v[i] = len(null_seen)
    null_beta, _, _ = _fit_heaps(null_cum_v)

    return DifferentiationResult(
        n_entries=n,
        distinct_sigs=n_distinct,
        heaps_beta=heaps_beta,
        heaps_K=heaps_K,
        heaps_r2=heaps_r2,
        null_heaps_beta=null_beta,
        diff_entropy=h_bits,
        diff_entropy_norm=h_norm,
        repetition_rate=rep_rate,
        novelty_rate=float(1.0 - rep_rate),
        cumulative_v=cum_v,
        differentiating=heaps_beta > 0.3,
    )


def analyse_from_telemetry() -> Optional[DifferentiationResult]:
    """Load John's real qualia stream and measure phenomenal differentiation."""
    entries = _load_qualia_entries()
    return analyse(entries)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No qualia stream found.")
    else:
        print(f"PhenomenalDifferentiator: {r.n_entries} entries")
        print(f"  Distinct signatures:  {r.distinct_sigs}  ({r.saturation_index:.2%} unique)")
        print(f"  Heaps β:              {r.heaps_beta:.4f}  (null {r.null_heaps_beta:.4f})")
        print(f"  Heaps K:              {r.heaps_K:.4f}  R²={r.heaps_r2:.4f}")
        print(f"  Diff entropy:         {r.diff_entropy:.4f} bits  (norm {r.diff_entropy_norm:.4f})")
        print(f"  Repetition rate:      {r.repetition_rate:.4f}")
        print(f"  Novelty rate:         {r.novelty_rate:.4f}")
        print(f"  Differentiating:      {r.differentiating}  (β > 0.3)")
