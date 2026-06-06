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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.snapshot import log_snapshot, snapshot_path


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
