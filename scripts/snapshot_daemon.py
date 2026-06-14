#!/usr/bin/env python3
"""
snapshot_daemon — standalone co-logger.

Samples all five adapters on a single timestamp at a fixed interval and appends to the
shared snapshot log, building a genuinely simultaneous multi-adapter time series for the
integration probe. Isolated from the consciousness heartbeat (no edits to the live
daemon); start/stop freely.

  python3 scripts/snapshot_daemon.py --interval 10        # log every 10s until killed
  python3 scripts/snapshot_daemon.py --once               # single sample

Note: phi channels only vary while the consciousness heartbeat is running; with the
heartbeat stopped, phi is frozen and the live variation comes from resources/memory/
decisions/interactions. Co-logged phi requires the heartbeat to be active.
"""
import argparse
import sys
import time
from pathlib import Path

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.snapshot import log_snapshot, snapshot_path

# Skip a snapshot cycle when system CPU is this hot; resume when it cools below RESUME
CPU_SKIP_PCT   = 80
CPU_RESUME_PCT = 60
CPU_POLL_S     = 10   # how often to re-check while throttled


def _cpu() -> float:
    return psutil.cpu_percent(interval=0.5)


def _wait_for_cpu() -> None:
    """Yield until CPU drops below CPU_RESUME_PCT, printing one message per hold."""
    notified = False
    while True:
        pct = _cpu()
        if pct < CPU_RESUME_PCT:
            if notified:
                print(f"[snapshot] CPU {pct:.0f}% — resuming", flush=True)
            return
        if not notified:
            print(f"[snapshot] CPU {pct:.0f}% >= {CPU_SKIP_PCT}% — throttling until <{CPU_RESUME_PCT}%",
                  flush=True)
            notified = True
        time.sleep(CPU_POLL_S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=10.0, help="seconds between samples")
    ap.add_argument("--once", action="store_true", help="log a single sample and exit")
    ap.add_argument("--max", type=int, default=0, help="stop after N samples (0 = forever)")
    a = ap.parse_args()

    path = snapshot_path()
    n = 0
    try:
        while True:
            # Yield to heavy work (agent log reads, IIT compute) before taking a snapshot
            if _cpu() >= CPU_SKIP_PCT:
                _wait_for_cpu()
            s = log_snapshot(path)
            n += 1
            print(f"[{n}] logged @ {time.strftime('%H:%M:%S')}  "
                  f"phi={s['phi_level']:+.4f} cpu={s['cpu_percent']:.0f}% "
                  f"mem={s['mem_percent']:.0f}% mem_vol={s['memory_volume']:.0f}", flush=True)
            if a.once or (a.max and n >= a.max):
                break
            time.sleep(a.interval)
    except KeyboardInterrupt:
        pass
    print(f"logged {n} snapshot(s) to {path}")


if __name__ == "__main__":
    main()
