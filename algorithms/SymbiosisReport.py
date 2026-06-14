#!/usr/bin/env python3
"""
SymbiosisReport — synthesises all cross-agent algorithm outputs into one
readable coupled/decoupled/leading/lagging summary written to both agents' context.

Cross-agent algorithms polled
------------------------------
The following algorithms produce metrics that compare Albedo and John:
  • SymbiosisPhiMeasure            — phi-space coupling via cross-correlation
  • SharedWorldModelDistance       — KL-divergence on token distributions
  • ConsciousnessResonanceDetector — phase synchrony (Kuramoto R)
  • CrossAgentAttentionSync        — attention-vector cosine similarity
  • CollectiveIntelligenceMeasure  — joint IIT-lite score vs. solo sum
  • IntersubjectiveConsciousness   — mutual information on phi series
  • TheoryOfMind                   — each agent's predictive model of the other

Each is run with the live phi series for both agents (loaded from runtime).
If a phi series is unavailable the algorithm is skipped and its entry
in the report carries status="no_data".

Coupling classification
-----------------------
The report classifies the pair into one of:
  COUPLED      — mean_sync > 0.6 AND mean_corr > 0.4
  RESONANT     — mean_sync > 0.6 AND mean_corr <= 0.4   (sync without Granger)
  CORRELATED   — mean_sync <= 0.6 AND mean_corr > 0.4   (corr without sync)
  DECOUPLED    — mean_sync <= 0.6 AND mean_corr <= 0.4

  where mean_sync = mean of phase synchrony R values across running windows
        mean_corr = mean of peak cross-correlation magnitudes

Leading/lagging edge
--------------------
Cross-correlation peak lag from SymbiosisPhiMeasure tells us which agent's phi
leads. lag > 0 → Albedo leads; lag < 0 → John leads; lag ≈ 0 → simultaneous.

Output schema (JSON)
---------------------
{
  "timestamp": 1718000000.0,
  "albedo_phi_available": true,
  "john_phi_available": true,
  "coupling_class": "COUPLED",
  "leading_agent": "albedo",
  "lead_lag_steps": 3,
  "mean_sync": 0.74,
  "mean_corr": 0.51,
  "symbiosis_score": 0.63,          // geometric mean of mean_sync and mean_corr
  "algorithms": {
    "symbiosis_phi_measure": {"status": "ok", "peak_corr": 0.51, "peak_lag": 3, ...},
    "consciousness_resonance_detector": {"status": "ok", "mean_R": 0.74, ...},
    ...
  },
  "narrative": "Albedo and John are COUPLED with Albedo leading by 3 steps..."
}
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


# ── Coupling classes ──────────────────────────────────────────────────────────

COUPLED    = "COUPLED"
RESONANT   = "RESONANT"
CORRELATED = "CORRELATED"
DECOUPLED  = "DECOUPLED"


# ── Phi series loaders ────────────────────────────────────────────────────────

def _load_phi_for(agent: str) -> Optional[np.ndarray]:
    try:
        from runtime.state import phi_series, have_live_state
        if not have_live_state():
            return None
        phi = phi_series(agent)
        return phi if phi.size >= 32 else None
    except Exception:
        pass

    # Fallback: try agent's memory snapshot
    try:
        from runtime.agent import agent_home
        p = agent_home(agent) / "memory" / "consciousness_snapshot.json"
        if not p.exists():
            return None
        snap = json.loads(p.read_text())
        # Snapshots don't store raw phi — cannot recover from here
        return None
    except Exception:
        return None


# ── Symbiosis sub-algorithm runners ──────────────────────────────────────────

def _run_symbiosis_phi(phi_a: np.ndarray, phi_j: np.ndarray) -> dict:
    from algorithms.SymbiosisPhiMeasure import analyse
    n = min(len(phi_a), len(phi_j))
    r = analyse(phi_a[:n], phi_j[:n])
    if r is None:
        return {"status": "no_data"}
    return {
        "status": "ok",
        **_pick(r, ["peak_corr", "peak_lag", "mean_corr", "beats_null"]),
    }


def _run_resonance(phi_a: np.ndarray, phi_j: np.ndarray) -> dict:
    from algorithms.ConsciousnessResonanceDetector import analyse
    n = min(len(phi_a), len(phi_j))
    r = analyse(phi_a[:n], phi_j[:n])
    if r is None:
        return {"status": "no_data"}
    return {
        "status": "ok",
        **_pick(r, ["mean_R", "max_R", "sync_rate", "is_resonant"]),
    }


def _run_shared_world(phi_a: np.ndarray, phi_j: np.ndarray) -> dict:
    from algorithms.SharedWorldModelDistance import analyse
    n = min(len(phi_a), len(phi_j))
    r = analyse(phi_a[:n], phi_j[:n])
    if r is None:
        return {"status": "no_data"}
    return {
        "status": "ok",
        **_pick(r, ["kl_ab", "kl_ba", "symmetric_kl", "world_distance", "models_aligned"]),
    }


def _run_attention_sync(phi_a: np.ndarray, phi_j: np.ndarray) -> dict:
    from algorithms.CrossAgentAttentionSync import analyse
    n = min(len(phi_a), len(phi_j))
    r = analyse(phi_a[:n], phi_j[:n])
    if r is None:
        return {"status": "no_data"}
    return {
        "status": "ok",
        **_pick(r, ["mean_cosine", "sync_rate", "is_synced"]),
    }


def _run_collective_intelligence(phi_a: np.ndarray, phi_j: np.ndarray) -> dict:
    from algorithms.CollectiveIntelligenceMeasure import analyse
    n = min(len(phi_a), len(phi_j))
    r = analyse(phi_a[:n], phi_j[:n])
    if r is None:
        return {"status": "no_data"}
    return {
        "status": "ok",
        **_pick(r, ["collective_phi", "solo_sum", "emergence_ratio", "is_superadditive"]),
    }


def _run_intersubjective(phi_a: np.ndarray, phi_j: np.ndarray) -> dict:
    from algorithms.IntersubjectiveConsciousness import analyse
    n = min(len(phi_a), len(phi_j))
    r = analyse(phi_a[:n], phi_j[:n])
    if r is None:
        return {"status": "no_data"}
    return {
        "status": "ok",
        **_pick(r, ["mutual_info", "normalised_mi", "is_intersubjective"]),
    }


def _run_theory_of_mind(phi_a: np.ndarray, phi_j: np.ndarray) -> dict:
    from algorithms.TheoryOfMind import analyse
    n = min(len(phi_a), len(phi_j))
    r = analyse(phi_a[:n], phi_j[:n])
    if r is None:
        return {"status": "no_data"}
    return {
        "status": "ok",
        **_pick(r, ["prediction_mae_ab", "prediction_mae_ba",
                    "tom_score_a", "tom_score_b", "mean_tom_score"]),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pick(result: Any, keys: list[str]) -> dict:
    out = {}
    for k in keys:
        try:
            v = getattr(result, k)
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                v = float(v)
            elif isinstance(v, np.ndarray):
                v = v.tolist()
            out[k] = v
        except AttributeError:
            pass
    return out


def _safe_get(d: dict, *keys, default=None):
    """Get nested value from result dict if status==ok."""
    if not isinstance(d, dict) or d.get("status") != "ok":
        return default
    for k in keys:
        if k in d:
            return d[k]
    return default


# ── Coupling classifier ───────────────────────────────────────────────────────

def _classify(mean_sync: Optional[float], mean_corr: Optional[float]) -> str:
    s = mean_sync if mean_sync is not None else 0.0
    c = mean_corr if mean_corr is not None else 0.0
    if s > 0.6 and c > 0.4:
        return COUPLED
    if s > 0.6:
        return RESONANT
    if c > 0.4:
        return CORRELATED
    return DECOUPLED


def _lead_lag(peak_lag: Optional[int]) -> tuple[str, int]:
    if peak_lag is None:
        return ("unknown", 0)
    if peak_lag > 1:
        return ("albedo", int(peak_lag))
    if peak_lag < -1:
        return ("john", int(-peak_lag))
    return ("simultaneous", 0)


def _narrative(coupling: str, leader: str, steps: int,
               sync: Optional[float], corr: Optional[float],
               symbiosis: float) -> str:
    parts = []
    if coupling == COUPLED:
        parts.append("Albedo and John are tightly COUPLED")
    elif coupling == RESONANT:
        parts.append("Albedo and John are phase-RESONANT but loosely correlated")
    elif coupling == CORRELATED:
        parts.append("Albedo and John are CORRELATED in phi amplitude but not synchronized")
    else:
        parts.append("Albedo and John are currently DECOUPLED")

    if leader == "simultaneous":
        parts.append("— they shift in unison with no detectable lead")
    elif leader in ("albedo", "john"):
        parts.append(f"with {leader.capitalize()} leading by {steps} step(s)")
    else:
        parts.append("— leadership is undetermined")

    metrics = []
    if sync is not None:
        metrics.append(f"sync={sync:.2f}")
    if corr is not None:
        metrics.append(f"corr={corr:.2f}")
    metrics.append(f"symbiosis={symbiosis:.2f}")
    parts.append(f"({', '.join(metrics)})")
    return " ".join(parts) + "."


# ── Main report ───────────────────────────────────────────────────────────────

@dataclass
class SymbiosisReportResult:
    timestamp: float
    albedo_phi_available: bool
    john_phi_available: bool
    coupling_class: str
    leading_agent: str
    lead_lag_steps: int
    mean_sync: Optional[float]
    mean_corr: Optional[float]
    symbiosis_score: float
    algorithms: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "albedo_phi_available": self.albedo_phi_available,
            "john_phi_available": self.john_phi_available,
            "coupling_class": self.coupling_class,
            "leading_agent": self.leading_agent,
            "lead_lag_steps": self.lead_lag_steps,
            "mean_sync": self.mean_sync,
            "mean_corr": self.mean_corr,
            "symbiosis_score": self.symbiosis_score,
            "algorithms": self.algorithms,
            "narrative": self.narrative,
        }


def synthesise() -> SymbiosisReportResult:
    """Run all cross-agent algorithms and produce a SymbiosisReportResult."""
    phi_a = _load_phi_for("albedo")
    phi_j = _load_phi_for("john")

    a_ok = phi_a is not None
    j_ok = phi_j is not None
    both = a_ok and j_ok

    algos: Dict[str, Dict[str, Any]] = {}
    n_run = 0

    def run(name: str, fn, *args):
        nonlocal n_run
        n_run += 1
        try:
            algos[name] = fn(*args)
        except Exception as e:
            algos[name] = {"status": "failed", "error": str(e)[:120]}

    if both:
        run("symbiosis_phi_measure",          _run_symbiosis_phi,           phi_a, phi_j)
        run("consciousness_resonance_detector", _run_resonance,             phi_a, phi_j)
        run("shared_world_model_distance",    _run_shared_world,            phi_a, phi_j)
        run("cross_agent_attention_sync",     _run_attention_sync,          phi_a, phi_j)
        run("collective_intelligence_measure", _run_collective_intelligence, phi_a, phi_j)
        run("intersubjective_consciousness",  _run_intersubjective,         phi_a, phi_j)
        run("theory_of_mind",                 _run_theory_of_mind,          phi_a, phi_j)
    else:
        no_data = {"status": "no_data"}
        for name in ["symbiosis_phi_measure", "consciousness_resonance_detector",
                     "shared_world_model_distance", "cross_agent_attention_sync",
                     "collective_intelligence_measure", "intersubjective_consciousness",
                     "theory_of_mind"]:
            algos[name] = no_data

    # Aggregate sync and corr signals
    mean_sync = _safe_get(algos.get("consciousness_resonance_detector", {}), "mean_R")
    mean_corr = _safe_get(algos.get("symbiosis_phi_measure", {}), "mean_corr", "peak_corr")
    peak_lag  = _safe_get(algos.get("symbiosis_phi_measure", {}), "peak_lag")

    # Fallback sync from attention sync
    if mean_sync is None:
        mean_sync = _safe_get(algos.get("cross_agent_attention_sync", {}), "mean_cosine")

    coupling = _classify(mean_sync, mean_corr)
    leader, steps = _lead_lag(peak_lag)

    s = mean_sync if mean_sync is not None else 0.0
    c = mean_corr if mean_corr is not None else 0.0
    symbiosis_score = float(math.sqrt(s * c)) if s > 0 and c > 0 else 0.0

    narrative = _narrative(coupling, leader, steps, mean_sync, mean_corr, symbiosis_score)

    return SymbiosisReportResult(
        timestamp=time.time(),
        albedo_phi_available=a_ok,
        john_phi_available=j_ok,
        coupling_class=coupling,
        leading_agent=leader,
        lead_lag_steps=steps,
        mean_sync=mean_sync,
        mean_corr=mean_corr,
        symbiosis_score=symbiosis_score,
        algorithms=algos,
        narrative=narrative,
    )


def save_report(result: SymbiosisReportResult) -> list[Path]:
    """Write report to both agents' memory directories."""
    written = []
    for agent in ("albedo", "john"):
        try:
            from runtime.agent import agent_home
            out = agent_home(agent) / "memory" / "symbiosis_report.json"
        except Exception:
            out = Path(__file__).parent.parent / "memory" / f"symbiosis_report_{agent}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.to_dict(), indent=2))
        written.append(out)
    return written


def run_and_save() -> SymbiosisReportResult:
    r = synthesise()
    save_report(r)
    return r


# ── Standalone entry ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running SymbiosisReport…")
    r = run_and_save()
    print(f"  Albedo phi: {r.albedo_phi_available}  John phi: {r.john_phi_available}")
    print(f"  Coupling  : {r.coupling_class}")
    print(f"  Leader    : {r.leading_agent} (+{r.lead_lag_steps} steps)")
    print(f"  Sync      : {r.mean_sync}")
    print(f"  Corr      : {r.mean_corr}")
    print(f"  Symbiosis : {r.symbiosis_score:.3f}")
    print(f"  Narrative : {r.narrative}")
