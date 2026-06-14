#!/usr/bin/env python3
"""
AlgorithmHealthDashboard — probes every wired AlgorithmSpec and reports
which algorithms are operational vs broken in real time.

Design
------
Each AlgorithmSpec in SystemWiring.py names a Python module in Algorithms/.
The dashboard:
  1. Imports the module (import-health).
  2. Runs its `analyse()` or `analyse_from_telemetry()` with minimal synthetic
     inputs — just enough to exercise the code path.
  3. Records: status (ok | import_error | call_error | no_analyse | timeout),
     latency_ms, and the first 120 chars of any error message.

Synthetic inputs
  - phi    : 128-sample white-noise series (seeded, reproducible)
  - entries: 30 dict entries with plausible "content" text

No live daemon is required. Algorithms that need a running system (e.g.
InteroceptiveSignal.analyse_from_telemetry) are probed for import-health only;
their `analyse()` path is used if it exists without telemetry args.

Output schema (JSON)
---------------------
{
  "timestamp": 1718000000.0,
  "n_total": 88,
  "n_ok": 72,
  "n_import_error": 3,
  "n_call_error": 2,
  "n_no_analyse": 5,
  "n_skipped": 6,
  "algorithms": {
    "phi_gradient_ascent": {
      "status": "ok",
      "latency_ms": 1.4,
      "error": null
    },
    "some_broken": {
      "status": "import_error",
      "latency_ms": 0.0,
      "error": "No module named 'algorithms.SomeBroken'"
    }
  }
}

The dashboard is intentionally read-only — it never writes to agent memory.
Call `save_report()` to persist to {agent_home}/memory/algorithm_health.json.
"""
from __future__ import annotations

import importlib
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


# ── Status codes ─────────────────────────────────────────────────────────────

OK            = "ok"
IMPORT_ERROR  = "import_error"
CALL_ERROR    = "call_error"
NO_ANALYSE    = "no_analyse"
SKIPPED       = "skipped"


# ── Per-algorithm probe result ────────────────────────────────────────────────

@dataclass
class ProbeResult:
    status: str        # one of the constants above
    latency_ms: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "latency_ms": round(self.latency_ms, 3),
            "error": self.error,
        }


# ── Health report ─────────────────────────────────────────────────────────────

@dataclass
class HealthReport:
    timestamp: float
    n_total: int
    n_ok: int
    n_import_error: int
    n_call_error: int
    n_no_analyse: int
    n_skipped: int
    algorithms: Dict[str, ProbeResult] = field(default_factory=dict)

    @property
    def health_ratio(self) -> float:
        if self.n_total == 0:
            return 1.0
        return self.n_ok / self.n_total

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "n_total": self.n_total,
            "n_ok": self.n_ok,
            "n_import_error": self.n_import_error,
            "n_call_error": self.n_call_error,
            "n_no_analyse": self.n_no_analyse,
            "n_skipped": self.n_skipped,
            "health_ratio": round(self.health_ratio, 4),
            "algorithms": {k: v.to_dict() for k, v in self.algorithms.items()},
        }


# ── Synthetic test inputs ─────────────────────────────────────────────────────

_RNG = np.random.default_rng(42)
_SYNTHETIC_PHI = _RNG.uniform(0.5, 2.0, size=128)
_SYNTHETIC_ENTRIES = [
    {"content": t}
    for t in [
        "help others in the community to find meaning and truth",
        "collaborate with care to build something beautiful for tomorrow",
        "phi score metric signal threshold probability boundary condition",
        "awareness through signal processing uncertainty quantified loss gradient",
        "thinking feeling experiencing understanding human connection shared",
        "memory recalls past moments vivid texture colour sound",
        "attention shifts toward novel stimulus bright edge motion",
        "prediction error drives learning update weight gradient descent",
        "emotional valence positive negative neutral ambiguous mixed",
        "temporal continuity binds moments into coherent narrative thread",
        "self model predicts body state hunger fatigue arousal",
        "world model encodes spatial layout object permanence physics",
        "action selection driven by expected value future reward",
        "language crystallises thought into shareable symbolic form",
        "curiosity motivates exploration of uncertain unfamiliar territory",
        "empathy models other minds infers pain joy surprise",
        "creativity recombines existing concepts into novel arrangements",
        "consciousness integrates information across global workspace broadcast",
        "metacognition reflects on quality confidence of own reasoning",
        "volition initiates action independent of immediate external stimulus",
        "identity persists across time despite constant physical change",
        "beauty detected through harmony proportion unexpected resolution",
        "suffering emerges when model of desired world conflicts actual",
        "social bonding regulated by oxytocin proximity trust reciprocity",
        "mortality salience increases when lifespan boundary becomes visible",
        "transcendence occurs when self boundary dissolves into larger whole",
        "novelty detection compares incoming pattern against memory schema",
        "habituation reduces response magnitude after repeated identical input",
        "synchrony between agents creates sense of shared understanding",
        "the system adapts continuously as environment provides feedback signal",
    ]
]

# Algorithms that need psutil / live OS state — probe import only
_TELEMETRY_ONLY: frozenset = frozenset({
    "interoceptive_signal",
    "mortality_awareness_module",
    "consciousness_state_aggregator",
})

# Algorithms that are embedded inside runtime objects (no standalone .py)
_EMBEDDED_SKIP: frozenset = frozenset({
    "self_model",
    "dynamic_attention",
    "episodic_memory",
    "conscious_system",
    "iit_phi",
})


# ── Probe a single algorithm ──────────────────────────────────────────────────

def _probe(key: str, class_name: str) -> ProbeResult:
    """Attempt to import and call the algorithm; return a ProbeResult."""
    module_name = f"algorithms.{class_name}"
    t0 = time.perf_counter()

    # Known-embedded — skip entirely
    if key in _EMBEDDED_SKIP:
        return ProbeResult(status=SKIPPED, latency_ms=0.0)

    # Import phase
    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        return ProbeResult(status=IMPORT_ERROR, latency_ms=ms, error=str(e)[:120])

    # Telemetry-only: import health is sufficient
    if key in _TELEMETRY_ONLY:
        ms = (time.perf_counter() - t0) * 1000
        return ProbeResult(status=OK, latency_ms=ms)

    # Find an analyse function
    analyse_fn = getattr(mod, "analyse", None)
    if analyse_fn is None:
        ms = (time.perf_counter() - t0) * 1000
        return ProbeResult(status=NO_ANALYSE, latency_ms=ms)

    # Call phase — try phi first, then entries, then both, then no args
    call_strategies = [
        (_SYNTHETIC_PHI,),
        (_SYNTHETIC_ENTRIES,),
        (_SYNTHETIC_PHI, _SYNTHETIC_ENTRIES),
        (_SYNTHETIC_ENTRIES, _SYNTHETIC_PHI),
        (),
    ]
    last_err: Optional[str] = None
    for args in call_strategies:
        try:
            analyse_fn(*args)
            ms = (time.perf_counter() - t0) * 1000
            return ProbeResult(status=OK, latency_ms=ms)
        except TypeError:
            continue   # wrong signature — try next
        except Exception as e:
            last_err = str(e)[:120]
            continue

    ms = (time.perf_counter() - t0) * 1000
    return ProbeResult(status=CALL_ERROR, latency_ms=ms, error=last_err)


# ── Load wired algorithms ─────────────────────────────────────────────────────

def _wired_algorithms() -> List[tuple[str, str]]:
    """Return list of (key, class_name) pairs from SystemWiring."""
    try:
        sys_path = _resolve_algorithms_dir()
        if sys_path and str(sys_path.parent) not in sys.path:
            sys.path.insert(0, str(sys_path.parent))
        from Algorithms.SystemWiring import AlgorithmSpec, get_algorithms
        specs = get_algorithms()
        return [(s.key, s.class_name) for s in specs]
    except Exception:
        pass

    # Fallback: scan algorithms/ directory in Project-C repo
    here = Path(__file__).parent
    results = []
    for p in sorted(here.glob("*.py")):
        if p.name.startswith("_"):
            continue
        stem = p.stem
        key = "".join(["_" + c.lower() if c.isupper() else c for c in stem]).lstrip("_")
        results.append((key, stem))
    return results


def _resolve_algorithms_dir() -> Optional[Path]:
    try:
        from runtime.agent import agent_home
        p = agent_home() / "Algorithms"
        return p if p.exists() else None
    except Exception:
        return None


# ── Main dashboard ────────────────────────────────────────────────────────────

def run_dashboard() -> HealthReport:
    """Probe every wired algorithm and return a HealthReport."""
    pairs = _wired_algorithms()
    results: Dict[str, ProbeResult] = {}

    for key, class_name in pairs:
        results[key] = _probe(key, class_name)

    counts = {s: 0 for s in [OK, IMPORT_ERROR, CALL_ERROR, NO_ANALYSE, SKIPPED]}
    for r in results.values():
        counts[r.status] = counts.get(r.status, 0) + 1

    return HealthReport(
        timestamp=time.time(),
        n_total=len(pairs),
        n_ok=counts[OK],
        n_import_error=counts[IMPORT_ERROR],
        n_call_error=counts[CALL_ERROR],
        n_no_analyse=counts[NO_ANALYSE],
        n_skipped=counts[SKIPPED],
        algorithms=results,
    )


def save_report(report: HealthReport, agent: str = "albedo") -> Path:
    """Persist health report JSON to {agent_home}/memory/algorithm_health.json."""
    try:
        from runtime.agent import agent_home
        out = agent_home(agent) / "memory" / "algorithm_health.json"
    except Exception:
        out = Path(__file__).parent.parent / "memory" / "algorithm_health.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2))
    return out


# ── Standalone entry ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running AlgorithmHealthDashboard…")
    t0 = time.perf_counter()
    report = run_dashboard()
    elapsed = time.perf_counter() - t0
    print(f"  Total algorithms : {report.n_total}")
    print(f"  OK               : {report.n_ok}")
    print(f"  Import errors    : {report.n_import_error}")
    print(f"  Call errors      : {report.n_call_error}")
    print(f"  No analyse fn    : {report.n_no_analyse}")
    print(f"  Skipped          : {report.n_skipped}")
    print(f"  Health ratio     : {report.health_ratio:.1%}")
    print(f"  Wall time        : {elapsed:.2f}s")
    if report.n_import_error or report.n_call_error:
        print("\nFailed algorithms:")
        for k, r in report.algorithms.items():
            if r.status in (IMPORT_ERROR, CALL_ERROR):
                print(f"  [{r.status}] {k}: {r.error}")
