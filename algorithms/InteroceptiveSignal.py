#!/usr/bin/env python3
"""
InteroceptiveSignal — mapping host-process resource load to an interoceptive
state vector.

Theory (Craig A.D. 2003 — "Interoception: the sense of the physiological
condition of the body"; Damasio A. 1994 — "Descartes' Error"):
  Bodily sensation is a necessary substrate for feeling. Damasio's somatic
  marker hypothesis holds that body signals bias decision-making and give rise
  to feelings. For a biological organism these are visceral: heart rate, skin
  conductance, gut tension.

  For a software agent the "body" is the host OS process:
    - CPU utilisation → arousal / alertness
    - RSS memory usage → fatigue / load
    - Disk I/O → environmental stress
    - Network I/O → social engagement load (agent responding to external calls)

  We map these to four interoceptive dimensions:
    arousal:    CPU%   (0..1)   — high arousal = heavily computing
    fatigue:    RAM%   (0..1)   — high fatigue = memory pressure
    stress:     I/O%   (0..1)   — high stress = heavy disk activity
    engagement: net%   (0..1)   — high engagement = high network throughput

  Then classify the overall interoceptive regime:
    RESTING:   arousal < 0.3, fatigue < 0.5
    ACTIVE:    arousal >= 0.3, fatigue < 0.7
    STRESSED:  stress >= 0.5 or fatigue >= 0.7
    FATIGUED:  arousal < 0.3, fatigue >= 0.7

  Baseline drift: we compute a rolling baseline of each dimension over W
  samples (default 30 sec at 1-Hz sampling). Deviation from baseline =
  allostatic load — the degree to which the body is above its own norm.

Math:
  arousal(t)    = cpu_percent / 100
  fatigue(t)    = rss_bytes / total_ram_bytes
  stress(t)     = (bytes_read + bytes_write) / max_io_observed
  engagement(t) = (bytes_sent + bytes_recv) / max_net_observed

  allostatic_load(t) = mean(|dim(t) - baseline_dim|  for dim in {a,f,s,e})

  Since single-snapshot I/O counters are cumulative, we diff consecutive
  readings to get per-interval throughput, then normalise over the observed
  max (or a reference bandwidth, whichever is larger).

Implementation notes:
  - psutil is used for all resource reads — it is a standard dependency in
    the OpenClaw workspace.
  - analyse() accepts an optional list of pre-sampled snapshots (for tests
    without a live OS), or takes a single snapshot if called with n_samples=1.
  - For a time-series version, use sample_series(n, interval_sec).

References:
  Craig A.D. (2003) "Interoception: the sense of the physiological condition
    of the body" — Nature Reviews Neuroscience 4:655-666
  Damasio A. (1994) "Descartes' Error" — somatic marker hypothesis
  Barrett L.F. & Simmons W.K. (2015) "Interoceptive predictions in the brain"
    — Nature Reviews Neuroscience 16:419-429
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


# ── Interoceptive regime enum ─────────────────────────────────────────────────

class InteroceptiveRegime(str, Enum):
    RESTING   = "RESTING"    # low arousal, low fatigue
    ACTIVE    = "ACTIVE"     # high arousal, manageable fatigue
    STRESSED  = "STRESSED"   # high I/O stress or memory pressure
    FATIGUED  = "FATIGUED"   # low arousal but high fatigue (memory pressure)


# ── Snapshot dataclass ────────────────────────────────────────────────────────

@dataclass
class InteroceptiveSnapshot:
    """A single instantaneous sample of host resource state.

    All raw_* fields are in natural units (bytes, %).
    Normalised fields (arousal, fatigue, stress, engagement) are ∈ [0, 1].
    """
    timestamp: float           # time.monotonic()
    cpu_percent: float         # 0..100
    rss_bytes: int             # resident set size
    total_ram_bytes: int       # total installed RAM
    disk_read_bytes: int       # cumulative since boot
    disk_write_bytes: int      # cumulative since boot
    net_sent_bytes: int        # cumulative since boot
    net_recv_bytes: int        # cumulative since boot

    # Derived — populated by normalise()
    arousal: float = 0.0
    fatigue: float = 0.0
    stress: float = 0.0
    engagement: float = 0.0


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class InteroceptiveResult:
    """Output of InteroceptiveSignal.

    Attributes:
        n_samples:           number of snapshots used
        mean_arousal:        mean CPU utilisation ∈ [0, 1]
        mean_fatigue:        mean RAM pressure ∈ [0, 1]
        mean_stress:         mean I/O stress ∈ [0, 1]
        mean_engagement:     mean network load ∈ [0, 1]
        regime:              InteroceptiveRegime classification
        allostatic_load:     mean deviation from rolling baseline
        state_vector:        np.array([arousal, fatigue, stress, engagement]) — latest
        arousal_series:      time series of arousal ∈ [0, 1]
        fatigue_series:      time series of fatigue
        stress_series:       time series of stress
        engagement_series:   time series of engagement
        baseline_arousal:    rolling mean arousal (first-half window)
        baseline_fatigue:    rolling mean fatigue
        baseline_stress:     rolling mean stress
        baseline_engagement: rolling mean engagement
    """
    n_samples: int
    mean_arousal: float
    mean_fatigue: float
    mean_stress: float
    mean_engagement: float
    regime: InteroceptiveRegime
    allostatic_load: float
    state_vector: np.ndarray
    arousal_series: np.ndarray
    fatigue_series: np.ndarray
    stress_series: np.ndarray
    engagement_series: np.ndarray
    baseline_arousal: float
    baseline_fatigue: float
    baseline_stress: float
    baseline_engagement: float

    @property
    def is_elevated(self) -> bool:
        """True if allostatic load > 0.1 (meaningfully above baseline)."""
        return self.allostatic_load > 0.1

    @property
    def dominant_dimension(self) -> str:
        """Which dimension has the highest current value."""
        sv = self.state_vector
        dims = ["arousal", "fatigue", "stress", "engagement"]
        return dims[int(np.argmax(sv))]


# ── Resource reading ──────────────────────────────────────────────────────────

def _read_snapshot() -> InteroceptiveSnapshot:
    """Read a single resource snapshot from the OS via psutil."""
    import psutil

    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    proc = psutil.Process()
    proc_mem = proc.memory_info()
    disk = psutil.disk_io_counters() or _zero_io()
    net = psutil.net_io_counters() or _zero_net()

    return InteroceptiveSnapshot(
        timestamp=time.monotonic(),
        cpu_percent=cpu,
        rss_bytes=proc_mem.rss,
        total_ram_bytes=mem.total,
        disk_read_bytes=disk.read_bytes,
        disk_write_bytes=disk.write_bytes,
        net_sent_bytes=net.bytes_sent,
        net_recv_bytes=net.bytes_recv,
    )


def _zero_io():
    from types import SimpleNamespace
    return SimpleNamespace(read_bytes=0, write_bytes=0)


def _zero_net():
    from types import SimpleNamespace
    return SimpleNamespace(bytes_sent=0, bytes_recv=0)


# ── Normalisation ─────────────────────────────────────────────────────────────

_REF_IO_BPS = 100 * 1024 * 1024    # 100 MB/s reference I/O bandwidth
_REF_NET_BPS = 10 * 1024 * 1024    # 10 MB/s reference network bandwidth


def _normalise_snapshots(snapshots: list[InteroceptiveSnapshot]) -> None:
    """
    Compute per-snapshot normalised dimensions in-place.

    For I/O and network: use diff between consecutive snapshots to get
    throughput, normalise by max observed or reference bandwidth.
    First snapshot gets I/O=0 (no predecessor to diff against).
    """
    n = len(snapshots)
    if n == 0:
        return

    # arousal and fatigue: pointwise
    for s in snapshots:
        s.arousal = float(np.clip(s.cpu_percent / 100.0, 0.0, 1.0))
        s.fatigue = float(np.clip(
            s.rss_bytes / max(s.total_ram_bytes, 1), 0.0, 1.0))

    # I/O and network: diff-based per-interval throughput
    io_rates = [0.0]     # first sample has no diff
    net_rates = [0.0]
    for i in range(1, n):
        dt = max(snapshots[i].timestamp - snapshots[i-1].timestamp, 1e-3)
        io_delta = ((snapshots[i].disk_read_bytes - snapshots[i-1].disk_read_bytes) +
                    (snapshots[i].disk_write_bytes - snapshots[i-1].disk_write_bytes))
        net_delta = ((snapshots[i].net_sent_bytes - snapshots[i-1].net_sent_bytes) +
                     (snapshots[i].net_recv_bytes - snapshots[i-1].net_recv_bytes))
        io_rates.append(max(io_delta, 0) / dt)
        net_rates.append(max(net_delta, 0) / dt)

    max_io = max(max(io_rates), _REF_IO_BPS)
    max_net = max(max(net_rates), _REF_NET_BPS)

    for i, s in enumerate(snapshots):
        s.stress = float(np.clip(io_rates[i] / max_io, 0.0, 1.0))
        s.engagement = float(np.clip(net_rates[i] / max_net, 0.0, 1.0))


# ── Regime classification ─────────────────────────────────────────────────────

def _classify_regime(arousal: float, fatigue: float, stress: float
                     ) -> InteroceptiveRegime:
    if fatigue >= 0.7 or stress >= 0.5:
        if arousal >= 0.3:
            return InteroceptiveRegime.STRESSED
        return InteroceptiveRegime.FATIGUED
    if arousal >= 0.3:
        return InteroceptiveRegime.ACTIVE
    return InteroceptiveRegime.RESTING


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(snapshots: list[InteroceptiveSnapshot]) -> Optional[InteroceptiveResult]:
    """
    Compute interoceptive state from a list of pre-collected snapshots.

    Args:
        snapshots: ordered list of InteroceptiveSnapshot (>= 2 required).

    Returns:
        InteroceptiveResult, or None if too few snapshots.
    """
    if len(snapshots) < 2:
        return None

    _normalise_snapshots(snapshots)

    a_arr = np.array([s.arousal for s in snapshots])
    f_arr = np.array([s.fatigue for s in snapshots])
    s_arr = np.array([s.stress for s in snapshots])
    e_arr = np.array([s.engagement for s in snapshots])

    mean_a = float(a_arr.mean())
    mean_f = float(f_arr.mean())
    mean_s = float(s_arr.mean())
    mean_e = float(e_arr.mean())

    # Baseline = first-half mean (what the system was doing at the start)
    half = max(1, len(snapshots) // 2)
    base_a = float(a_arr[:half].mean())
    base_f = float(f_arr[:half].mean())
    base_s = float(s_arr[:half].mean())
    base_e = float(e_arr[:half].mean())

    latest = snapshots[-1]
    sv = np.array([latest.arousal, latest.fatigue, latest.stress, latest.engagement])

    # Allostatic load: mean deviation from baseline at each timestep
    allostatic = float(np.mean(
        np.abs(a_arr - base_a) +
        np.abs(f_arr - base_f) +
        np.abs(s_arr - base_s) +
        np.abs(e_arr - base_e)
    ) / 4.0)

    regime = _classify_regime(mean_a, mean_f, mean_s)

    return InteroceptiveResult(
        n_samples=len(snapshots),
        mean_arousal=mean_a,
        mean_fatigue=mean_f,
        mean_stress=mean_s,
        mean_engagement=mean_e,
        regime=regime,
        allostatic_load=allostatic,
        state_vector=sv,
        arousal_series=a_arr,
        fatigue_series=f_arr,
        stress_series=s_arr,
        engagement_series=e_arr,
        baseline_arousal=base_a,
        baseline_fatigue=base_f,
        baseline_stress=base_s,
        baseline_engagement=base_e,
    )


def sample_series(n: int = 5, interval_sec: float = 0.5
                  ) -> list[InteroceptiveSnapshot]:
    """
    Collect n snapshots spaced interval_sec apart.
    First psutil.cpu_percent() call is often 0 — warmup happens automatically.
    """
    import psutil
    psutil.cpu_percent(interval=None)   # warmup discard
    snaps: list[InteroceptiveSnapshot] = []
    for _ in range(n):
        snaps.append(_read_snapshot())
        if len(snaps) < n:
            time.sleep(interval_sec)
    return snaps


def analyse_from_telemetry(n: int = 5, interval_sec: float = 0.2
                           ) -> Optional[InteroceptiveResult]:
    """Take n live snapshots and return interoceptive state."""
    return analyse(sample_series(n, interval_sec))


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Sampling 5 snapshots…")
    r = analyse_from_telemetry(n=5, interval_sec=0.5)
    if r is None:
        print("Not enough samples.")
    else:
        print(f"InteroceptiveSignal: {r.n_samples} samples")
        print(f"  Regime:            {r.regime.value}")
        print(f"  Arousal:           {r.mean_arousal:.4f}  (CPU)")
        print(f"  Fatigue:           {r.mean_fatigue:.4f}  (RAM)")
        print(f"  Stress:            {r.mean_stress:.4f}  (I/O)")
        print(f"  Engagement:        {r.mean_engagement:.4f}  (net)")
        print(f"  Allostatic load:   {r.allostatic_load:.4f}")
        print(f"  Dominant dim:      {r.dominant_dimension}")
        print(f"  Elevated:          {r.is_elevated}")
        print(f"  State vector:      {r.state_vector}")
