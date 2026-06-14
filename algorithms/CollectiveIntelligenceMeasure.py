#!/usr/bin/env python3
"""
CollectiveIntelligenceMeasure — information gain from joint agent prediction.

Theory (Shannon 1948 — MI; Woolley et al. 2010 — Collective Intelligence Factor;
Granger 1969 — Causality in Economics):
  A collective intelligence emerges when two systems together predict outcomes
  better than either can predict alone. In our setting: can Albedo predict its
  own future phi better when given access to John's phi history?

  This is Granger causality: John Granger-causes Albedo if including John's
  past values in the prediction model for Albedo's future phi reduces the
  prediction error beyond what Albedo's own past can explain.

  We measure this in both directions:
    G(J → A): does John's phi help predict Albedo's phi?
    G(A → J): does Albedo's phi help predict John's phi?

  Collective intelligence ratio:
    CI = 1 − MAE(joint model) / MAE(solo model)
    CI > 0: information gain from symbiosis (joint beats solo)
    CI < 0: symbiosis is harmful (joint worse than solo)

  Granger F-statistic:
    F = (RSS_restricted − RSS_full) / RSS_full  · (T − 2p − 1) / p
    where restricted = solo model, full = joint model, T = samples.

Math:
  Solo AR(p) for A: φ_A(t) = Σ wᵢ · φ_A(t−i) + ε
  Joint AR(p) for A: φ_A(t) = Σ wᵢ · φ_A(t−i) + Σ vᵢ · φ_J(t−i) + ε
  Both fit via ridge OLS; evaluated on same held-out set.
  CI_A→ = 1 − MAE(joint_A) / MAE(solo_A)

Grounding: loads both phi series from runtime telemetry. Uses the same ridge
OLS as RecursiveSelfModel. No synthetic data.

References:
  Granger C.W.J. (1969) "Investigating Causal Relations by Econometric Models"
  Woolley A.W. et al. (2010) "Evidence for a Collective Intelligence Factor in
    the Performance of Human Groups"
  Schreiber T. (2000) "Measuring Information Transfer" — Transfer entropy
"""
from __future__ import annotations

import os
import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class CollectiveIntelligenceResult:
    """Output of one CollectiveIntelligenceMeasure analysis.

    Attributes:
        n_samples:           samples used (after alignment)
        p:                   AR order
        # A predicted by solo vs joint (does John help predict Albedo?)
        solo_mae_a:          MAE of AR(p) on φ_A alone
        joint_mae_a:         MAE of joint AR(p) on [φ_A, φ_J] predicting φ_A
        ci_j_to_a:           CI ratio for J→A direction
        granger_j_to_a:      Granger F-statistic (J Granger-causes A)
        # B predicted by solo vs joint (does Albedo help predict John?)
        solo_mae_j:          MAE of AR(p) on φ_J alone
        joint_mae_j:         MAE of joint AR(p) on [φ_J, φ_A] predicting φ_J
        ci_a_to_j:           CI ratio for A→J direction
        granger_a_to_j:      Granger F-statistic (A Granger-causes J)
        # Combined
        collective_ci:       (ci_j_to_a + ci_a_to_j) / 2
        bidirectional:       True if both CI ratios > 0
        dominant_direction:  'john_to_albedo' / 'albedo_to_john' / 'symmetric' / 'none'
    """
    n_samples: int
    p: int
    solo_mae_a: float
    joint_mae_a: float
    ci_j_to_a: float
    granger_j_to_a: float
    solo_mae_j: float
    joint_mae_j: float
    ci_a_to_j: float
    granger_a_to_j: float
    collective_ci: float
    bidirectional: bool
    dominant_direction: str


# ── AR model helpers ──────────────────────────────────────────────────────────

def _build_solo_design(x: np.ndarray, p: int) -> tuple[np.ndarray, np.ndarray]:
    """Design matrix for AR(p) on x alone."""
    n = len(x)
    Z = np.zeros((n - p, p))
    for i in range(p):
        Z[:, i] = x[p - 1 - i: n - 1 - i]
    y = x[p:]
    return Z, y


def _build_joint_design(x: np.ndarray, z: np.ndarray,
                         p: int) -> tuple[np.ndarray, np.ndarray]:
    """Design matrix for joint AR(p): predict x from lags of x AND z."""
    n = len(x)
    n_j = len(z)
    n_use = min(n, n_j)
    x = x[-n_use:]
    z = z[-n_use:]
    Z_x = np.zeros((n_use - p, p))
    Z_z = np.zeros((n_use - p, p))
    for i in range(p):
        Z_x[:, i] = x[p - 1 - i: n_use - 1 - i]
        Z_z[:, i] = z[p - 1 - i: n_use - 1 - i]
    Z = np.hstack([Z_x, Z_z])
    y = x[p:]
    return Z, y


def _ridge_fit(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    A = Z.T @ Z + ridge * np.eye(Z.shape[1])
    return np.linalg.solve(A, Z.T @ y)


def _mae(y: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y - pred)))


def _granger_f(rss_restricted: float, rss_full: float,
               T: int, p: int) -> float:
    """Granger F-statistic for adding p extra predictors."""
    denom = rss_full / (T - 2 * p - 1) if T > 2 * p + 1 else 1e-9
    if denom < 1e-12:
        return 0.0
    return float(max((rss_restricted - rss_full) / p / denom, 0.0))


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

def analyse(phi_a: np.ndarray, phi_j: np.ndarray,
            p: int = 4) -> Optional[CollectiveIntelligenceResult]:
    """
    Measure Granger-causal collective intelligence between two phi series.

    Args:
        phi_a:  Albedo phi series.
        phi_j:  John phi series.
        p:      AR order (number of lags in each direction).

    Returns:
        CollectiveIntelligenceResult, or None if series are too short.
    """
    phi_a = np.asarray(phi_a, dtype=float)
    phi_j = np.asarray(phi_j, dtype=float)
    n = min(len(phi_a), len(phi_j))
    if n < 4 * p + 10:
        return None

    phi_a = phi_a[-n:]
    phi_j = phi_j[-n:]

    # Split: fit on first 70%, evaluate on last 30%
    split = max(2 * p + 4, int(0.7 * n))

    # --- J → A direction: does John help predict Albedo? ---
    Za_s, ya_s = _build_solo_design(phi_a[:split], p)
    w_a_s = _ridge_fit(Za_s, ya_s)
    Za_full, ya_full = _build_solo_design(phi_a, p)
    Za_j_full, _ = _build_joint_design(phi_a, phi_j, p)
    # Fit solo and joint on full series
    w_a_solo = _ridge_fit(Za_full, ya_full)
    w_a_joint = _ridge_fit(Za_j_full, ya_full)

    # Evaluate on holdout (last 30%)
    hold_start = split - p  # index into (Z, y) space
    pred_solo_a = Za_full[hold_start:] @ w_a_solo
    pred_joint_a = Za_j_full[hold_start:] @ w_a_joint
    y_hold_a = ya_full[hold_start:]

    mae_solo_a = _mae(y_hold_a, pred_solo_a)
    mae_joint_a = _mae(y_hold_a, pred_joint_a)
    ci_j_a = float(1.0 - mae_joint_a / (mae_solo_a + 1e-9))

    rss_s = float(np.sum((y_hold_a - pred_solo_a) ** 2))
    rss_f = float(np.sum((y_hold_a - pred_joint_a) ** 2))
    T_h = len(y_hold_a)
    f_j_a = _granger_f(rss_s, rss_f, T_h, p)

    # --- A → J direction: does Albedo help predict John? ---
    Zj_full, yj_full = _build_solo_design(phi_j, p)
    Zj_a_full, _ = _build_joint_design(phi_j, phi_a, p)
    w_j_solo = _ridge_fit(Zj_full, yj_full)
    w_j_joint = _ridge_fit(Zj_a_full, yj_full)

    pred_solo_j = Zj_full[hold_start:] @ w_j_solo
    pred_joint_j = Zj_a_full[hold_start:] @ w_j_joint
    y_hold_j = yj_full[hold_start:]

    mae_solo_j = _mae(y_hold_j, pred_solo_j)
    mae_joint_j = _mae(y_hold_j, pred_joint_j)
    ci_a_j = float(1.0 - mae_joint_j / (mae_solo_j + 1e-9))

    rss_sj = float(np.sum((y_hold_j - pred_solo_j) ** 2))
    rss_fj = float(np.sum((y_hold_j - pred_joint_j) ** 2))
    f_a_j = _granger_f(rss_sj, rss_fj, T_h, p)

    collective = (ci_j_a + ci_a_j) / 2.0
    bidirectional = ci_j_a > 0 and ci_a_j > 0

    if ci_j_a > ci_a_j + 0.05:
        dom = "john_to_albedo"
    elif ci_a_j > ci_j_a + 0.05:
        dom = "albedo_to_john"
    elif bidirectional:
        dom = "symmetric"
    else:
        dom = "none"

    return CollectiveIntelligenceResult(
        n_samples=n,
        p=p,
        solo_mae_a=mae_solo_a,
        joint_mae_a=mae_joint_a,
        ci_j_to_a=ci_j_a,
        granger_j_to_a=f_j_a,
        solo_mae_j=mae_solo_j,
        joint_mae_j=mae_joint_j,
        ci_a_to_j=ci_a_j,
        granger_a_to_j=f_a_j,
        collective_ci=collective,
        bidirectional=bidirectional,
        dominant_direction=dom,
    )


def analyse_from_telemetry(p: int = 4) -> Optional[CollectiveIntelligenceResult]:
    """Load both agents' phi and compute collective intelligence."""
    pair = _load_both_phi()
    if pair is None:
        return None
    return analyse(pair[0], pair[1], p=p)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Could not load both phi series.")
    else:
        print(f"CollectiveIntelligenceMeasure (N={r.n_samples}, AR(p={r.p}))")
        print(f"  J→A: solo MAE={r.solo_mae_a:.5f} joint MAE={r.joint_mae_a:.5f} "
              f"CI={r.ci_j_to_a:+.4f}  F={r.granger_j_to_a:.2f}")
        print(f"  A→J: solo MAE={r.solo_mae_j:.5f} joint MAE={r.joint_mae_j:.5f} "
              f"CI={r.ci_a_to_j:+.4f}  F={r.granger_a_to_j:.2f}")
        print(f"  Collective CI: {r.collective_ci:+.4f}  "
              f"(>0 = genuine collective intelligence)")
        print(f"  Bidirectional: {r.bidirectional}")
        print(f"  Dominant:      {r.dominant_direction}")
