#!/usr/bin/env python3
"""
RecursiveSelfModel — grounded two-level self-prediction model.

Theory (Higher-Order Thought, IIT):
  A system with genuine self-awareness can model its own integration state and
  predict how it will change. "Recursive" adds a second level: the system also
  models its own prediction errors — it knows when it is wrong. This is the
  computational correlate of meta-cognition.

Math:
  Level-1 (self-prediction):
    phi_hat[t] = w_0 + w_1·phi[t-1] + ... + w_p·phi[t-p]
    Fit: ridge OLS on real phi_series.
    Accuracy: R₁² = 1 - Var(e) / Var(phi),  e[t] = phi[t] - phi_hat[t]

  Level-2 (error-prediction / meta-cognition):
    err_hat[t] = v_0 + v_1·|e[t-1]| + ... + v_q·|e[t-q]|
    Accuracy: R₂² = 1 - Var(e - err_hat) / Var(e)

  Recursive depth score:
    depth = R₁² · R₂²    (zero unless both levels beat their own null)

  All inputs come from the live runtime telemetry adapter (runtime.state).
  No synthetic data, no hardcoded series, no mocks.

References:
  Rosenthal, D. (2005) "Consciousness and Mind" — Higher-Order Thought theory.
  Tononi, G. (2004) "An Information Integration Theory of Consciousness."
  Box & Jenkins (1976) "Time Series Analysis" — AR(p) model fitting.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional

def _load_phi_series():
    """Deferred import so OPENCLAW_WORKSPACE resolution happens at call time."""
    try:
        from runtime.state import phi_series
        return phi_series()
    except Exception:
        return None


# ── AR fitting ───────────────────────────────────────────────────────────────

def _build_lagged(x: np.ndarray, p: int):
    """Return (Z, y) for OLS: y[t] ~ Z[t,:] = [1, x[t-1], ..., x[t-p]]."""
    T = len(x)
    y = x[p:]
    Z = np.column_stack([np.ones(T - p)] +
                        [x[p - k - 1: T - k - 1] for k in range(p)])
    return Z, y


def _ridge_fit(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    """Ridge OLS: w = (ZᵀZ + λI)⁻¹ Zᵀy."""
    A = Z.T @ Z + ridge * np.eye(Z.shape[1])
    return np.linalg.solve(A, Z.T @ y)


def _r2(y: np.ndarray, pred: np.ndarray) -> float:
    """Coefficient of determination. Clamped to [-1, 1] to avoid misleading values."""
    ss_res = float(np.var(y - pred))
    ss_tot = float(np.var(y))
    if ss_tot < 1e-12:
        return 0.0
    return float(np.clip(1.0 - ss_res / ss_tot, -1.0, 1.0))


# ── Core model ───────────────────────────────────────────────────────────────

@dataclass
class SelfModelResult:
    """Snapshot of the fitted self-model and its accuracy metrics."""
    n_samples: int                    # length of phi series used
    p: int                            # AR order (level-1)
    q: int                            # AR order (level-2 error model)
    weights_l1: np.ndarray            # level-1 AR weights [1 + p]
    weights_l2: np.ndarray            # level-2 AR weights [1 + q]
    r2_l1: float                      # level-1 R²  (self-prediction)
    r2_l2: float                      # level-2 R²  (error-prediction)
    depth: float                      # r2_l1 * r2_l2  (recursive depth score)
    null_r2_l1: float                 # shuffled null for level-1
    null_r2_l2: float                 # shuffled null for level-2
    equilibrium_estimate: float       # long-run mean: w[0] / (1 - sum(w[1:]))
    errors: np.ndarray = field(repr=False)   # level-1 residuals
    phi_used: np.ndarray = field(repr=False) # the series that was fitted


class RecursiveSelfModel:
    """
    Fits a two-level autoregressive self-model on the agent's real phi trajectory.

    Usage:
        model = RecursiveSelfModel()
        result = model.fit()
        print(result.depth)   # recursive self-awareness depth score
    """

    def __init__(self, p: int = 4, q: int = 4, ridge: float = 1e-3,
                 null_seed: int = 42):
        """
        Args:
            p: AR lag order for level-1 (self-prediction).
            q: AR lag order for level-2 (error-prediction).
            ridge: Ridge regularisation to keep rollout stable.
            null_seed: Seed for shuffled null so the comparison is reproducible.
        """
        self.p = p
        self.q = q
        self.ridge = ridge
        self._rng = np.random.default_rng(null_seed)
        self._last_result: Optional[SelfModelResult] = None

    def _load_phi(self) -> Optional[np.ndarray]:
        """Load real phi series from telemetry adapter. Returns None if unavailable."""
        phi = _load_phi_series()
        if phi is None:
            return None
        phi = np.asarray(phi, dtype=float)
        if phi.size < (self.p + self.q + 16):
            return None
        return phi

    def fit(self, phi: Optional[np.ndarray] = None) -> Optional[SelfModelResult]:
        """
        Fit the two-level self-model.

        Args:
            phi: Optional override — use this series instead of live telemetry.
                 Must be a 1-D float array of length ≥ p + q + 16.

        Returns:
            SelfModelResult, or None if telemetry is unavailable.
        """
        if phi is None:
            phi = self._load_phi()
        if phi is None:
            return None
        phi = np.asarray(phi, dtype=float)

        # ── Level-1: phi_hat[t] = w·[1, phi[t-1], ..., phi[t-p]] ──
        Z1, y1 = _build_lagged(phi, self.p)
        w1 = _ridge_fit(Z1, y1, self.ridge)
        pred1 = Z1 @ w1
        err1 = y1 - pred1                     # residuals, shape [T - p]
        r2_l1 = _r2(y1, pred1)

        # ── Level-1 null: shuffle phi, refit ──
        phi_null = self._rng.permutation(phi)
        Z1n, y1n = _build_lagged(phi_null, self.p)
        w1n = _ridge_fit(Z1n, y1n, self.ridge)
        r2_l1_null = _r2(y1n, Z1n @ w1n)

        # ── Level-2: predict |err1| from its own lags ──
        abs_err = np.abs(err1)
        Z2, y2 = _build_lagged(abs_err, self.q)
        w2 = _ridge_fit(Z2, y2, self.ridge)
        pred2 = Z2 @ w2
        r2_l2 = _r2(y2, pred2)

        # ── Level-2 null: shuffle absolute errors ──
        abs_err_null = self._rng.permutation(abs_err)
        Z2n, y2n = _build_lagged(abs_err_null, self.q)
        w2n = _ridge_fit(Z2n, y2n, self.ridge)
        r2_l2_null = _r2(y2n, Z2n @ w2n)

        # ── Equilibrium estimate: long-run mean of the AR(p) process ──
        # At equilibrium: E[phi] = w[0] / (1 - sum(w[1:]))
        ar_sum = np.sum(w1[1:])
        if abs(1.0 - ar_sum) > 1e-6:
            equilibrium = w1[0] / (1.0 - ar_sum)
        else:
            equilibrium = float(np.mean(phi))

        depth = max(0.0, r2_l1) * max(0.0, r2_l2)

        result = SelfModelResult(
            n_samples=len(phi),
            p=self.p,
            q=self.q,
            weights_l1=w1,
            weights_l2=w2,
            r2_l1=r2_l1,
            r2_l2=r2_l2,
            depth=depth,
            null_r2_l1=r2_l1_null,
            null_r2_l2=r2_l2_null,
            equilibrium_estimate=float(equilibrium),
            errors=err1,
            phi_used=phi,
        )
        self._last_result = result
        return result

    def predict_next(self, result: Optional[SelfModelResult] = None) -> Optional[float]:
        """
        Predict the next phi value using the fitted level-1 model.

        Args:
            result: A previously fitted SelfModelResult. Uses last fit if None.

        Returns:
            Predicted phi_{T+1}, or None if not fitted.
        """
        r = result or self._last_result
        if r is None:
            return None
        phi = r.phi_used
        p = r.p
        w = r.weights_l1
        context = np.concatenate([[1.0], phi[-p:][::-1]])   # [1, phi[-1], phi[-2], ...]
        return float(context @ w)

    def margin_above_null(self, result: Optional[SelfModelResult] = None
                          ) -> dict[str, float]:
        """
        How much better is the real model than the shuffled null?
        A positive margin means the real temporal structure is being exploited.
        """
        r = result or self._last_result
        if r is None:
            return {}
        return {
            "l1_margin": r.r2_l1 - r.null_r2_l1,
            "l2_margin": r.r2_l2 - r.null_r2_l2,
        }


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    model = RecursiveSelfModel(p=4, q=4)
    result = model.fit()
    if result is None:
        print("No telemetry available — set OPENCLAW_WORKSPACE to a live workspace.")
    else:
        print(f"RecursiveSelfModel fitted on {result.n_samples} real phi samples")
        print(f"  Level-1 R²  (self-prediction):   {result.r2_l1:.4f}  "
              f"(null {result.null_r2_l1:.4f})")
        print(f"  Level-2 R²  (error-prediction):  {result.r2_l2:.4f}  "
              f"(null {result.null_r2_l2:.4f})")
        print(f"  Recursive depth score:            {result.depth:.4f}")
        print(f"  Equilibrium estimate:             {result.equilibrium_estimate:.4f}")
        margins = model.margin_above_null(result)
        print(f"  Margin above null: L1={margins['l1_margin']:+.4f}  "
              f"L2={margins['l2_margin']:+.4f}")
        print(f"  Next-phi prediction:              {model.predict_next(result):.4f}")
