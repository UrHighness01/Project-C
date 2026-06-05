#!/usr/bin/env python3
"""
Cross-adapter integration probe.

Tests whether the agent's real signal sources are genuinely *coupled* (one integrated
system) or independent (decoration). Event-aligned on the phi heartbeat clock (highest
resolution); each slower adapter contributes its most-recent value before each heartbeat
(last-carry-forward, no resampling/hallucination). We compute the cross-adapter transfer-
entropy matrix and collapse it to an effective-information (EI) score, then compare to a
shuffled null. EI >> null => the parts genuinely interact.

Honest scope: phi telemetry is a dense 24h window; memory/decision/interaction signals
are sparse and largely outside it, so their coverage is reported and low-coverage/zero-
variance channels are dropped. A full 5-way integration measurement needs all adapters
logged on a shared clock going forward -- a concrete recommendation, not a fudge.
"""
from __future__ import annotations

from datetime import datetime
import numpy as np

from runtime.state import load_daemon_state
from runtime.memory_store import journals
from runtime.interactions import turns as interaction_turns, lexicon_sentiment
from runtime.decisions import corrections
# (Granger causality used directly; the histogram TE estimator returns ~0 on dense signals)


def _ts(s: str) -> float:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return 0.0


def _carry_forward(base_t: np.ndarray, ev_t: np.ndarray, ev_v: np.ndarray) -> np.ndarray:
    """For each base timestamp, the most recent event value at or before it (else nan)."""
    out = np.full(base_t.size, np.nan)
    if ev_t.size == 0:
        return out
    order = np.argsort(ev_t); ev_t, ev_v = ev_t[order], ev_v[order]
    idx = np.searchsorted(ev_t, base_t, side="right") - 1
    valid = idx >= 0
    out[valid] = ev_v[idx[valid]]
    return out


def build_channels():
    """Return (names, [C,T] matrix, coverage dict) of event-aligned real channels."""
    st = load_daemon_state()
    h = (st or {}).get("phi_history", []) or []
    if len(h) < 32:
        return [], np.zeros((0, 0)), {}
    base_t = np.array([_ts(e.get("timestamp")) for e in h])
    chans = {
        "phi_level": np.array([e.get("phi_accumulated", 0.0) for e in h]),
        "phi_delta": np.array([e.get("phi_delta", 0.0) for e in h]),
        "compute_load": np.array([e.get("execution_time", 0.0) for e in h]),
    }
    # slow adapters, carried forward onto the heartbeat clock
    js = journals()
    chans["memory_volume"] = _carry_forward(
        base_t, np.array([_ts(d.isoformat()) for d, _, _ in js]),
        np.cumsum([sz for _, _, sz in js]).astype(float) if js else np.zeros(0))
    cs = corrections()
    chans["decisions"] = _carry_forward(
        base_t, np.array([_ts(c.get("created_at")) for c in cs]),
        np.arange(1, len(cs) + 1, dtype=float) if cs else np.zeros(0))
    ts = interaction_turns()
    chans["interaction_sentiment"] = _carry_forward(
        base_t, np.array([t["ts"] for t in ts]),
        np.array([lexicon_sentiment(t.get("user_text", "")) for t in ts]) if ts else np.zeros(0))

    names, rows, cov = [], [], {}
    for n, v in chans.items():
        finite = np.isfinite(v)
        coverage = finite.mean()
        varies = finite.sum() > 8 and np.nanstd(v) > 1e-9
        cov[n] = {"coverage": float(coverage), "varies": bool(varies)}
        if varies:
            vv = v.copy(); vv[~finite] = np.nanmedian(v[finite])
            names.append(n); rows.append(vv)
    return names, (np.vstack(rows) if rows else np.zeros((0, base_t.size))), cov


def _granger(x: np.ndarray, y: np.ndarray, lag: int = 3) -> float:
    """Directed coupling X->Y via Granger causality: how much X's past reduces the
    prediction error on Y beyond Y's own past. The linear analog of transfer entropy,
    robust on continuous signals (the histogram TE estimator returns ~0 on 1000 dense
    samples). Returns log(SSE_reduced / SSE_full) >= 0."""
    x = (x - x.mean()) / (x.std() + 1e-12)
    y = (y - y.mean()) / (y.std() + 1e-12)
    n = y.size
    if n <= lag + 5:
        return 0.0
    Y = y[lag:]
    yp = np.column_stack([y[lag - k - 1:n - k - 1] for k in range(lag)])
    xp = np.column_stack([x[lag - k - 1:n - k - 1] for k in range(lag)])
    def sse(design):
        D = np.column_stack([np.ones(len(Y)), design])
        beta, *_ = np.linalg.lstsq(D, Y, rcond=None)
        return float(((Y - D @ beta) ** 2).sum())
    sse_r = sse(yp)                          # Y from its own past
    sse_f = sse(np.column_stack([yp, xp]))   # Y from its past + X's past
    if sse_f <= 0 or sse_r <= 0:
        return 0.0
    return max(0.0, np.log(sse_r / sse_f))


def te_matrix(M: np.ndarray) -> np.ndarray:
    """Directed coupling matrix (row i -> col j) via Granger causality."""
    C = M.shape[0]
    G = np.zeros((C, C))
    for i in range(C):
        for j in range(C):
            if i != j:
                G[i, j] = _granger(M[i], M[j])
    return G


def effective_information(TE: np.ndarray) -> float:
    """John's EI: entropy of the whole normalised coupling matrix minus the summed
    per-row entropies. High when coupling is both present and differentiated."""
    flat = TE.flatten()
    if flat.sum() <= 0:
        return 0.0

    def H(p):
        p = np.asarray(p, float); s = p.sum()
        if s <= 0:
            return 0.0
        p = p[p > 0] / s
        return float(-(p * np.log2(p)).sum())

    return H(flat) - sum(H(TE[i]) for i in range(TE.shape[0]))


def main():
    names, M, cov = build_channels()
    print("=== Adapter coverage on the phi heartbeat clock ===")
    for n, c in cov.items():
        print(f"  {n:22s} coverage={c['coverage']*100:5.1f}%  usable={c['varies']}")
    if M.shape[0] < 2:
        print("\nInsufficient simultaneously-varying channels for an integration measure.")
        print("Recommendation: log all adapters on a shared clock to enable full 5-way EI.")
        return
    print(f"\n=== Coupling among {M.shape[0]} usable channels: {names} ===")
    TE = te_matrix(M)
    np.set_printoptions(precision=4, suppress=True)
    print("Granger-causality coupling matrix (row -> col):\n", TE)
    ei = effective_information(TE)
    rng = np.random.default_rng(0)
    null = []
    for _ in range(200):
        Ms = np.vstack([rng.permutation(M[i]) for i in range(M.shape[0])])
        null.append(effective_information(te_matrix(Ms)))
    null = np.array(null)
    z = (ei - null.mean()) / (null.std() + 1e-9)
    print(f"\nintegration EI       = {ei:.4f}")
    print(f"shuffled null EI     = {null.mean():.4f} +/- {null.std():.4f}")
    print(f"z-score vs null      = {z:.2f}")
    print(f"verdict: {'genuine coupling (EI >> null)' if z > 3 else 'not clearly above chance'}")


if __name__ == "__main__":
    main()
