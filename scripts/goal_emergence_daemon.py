#!/usr/bin/env python3
"""
goal_emergence_daemon — let real goals emerge from live conversation.

Periodically runs the grounded emergence check for each agent: when a drive is genuinely
unmet AND the agent has dwelt on a salient, novel topic in real conversation, a properly-
formed goal is written to that agent's goal-state.json (see goal_emergence.maybe_emerge_goal).

It is self-limiting -- emergence is gated on real drive tension and topic novelty, and a
topic already represented as a goal is skipped -- so it does not spam. Every goal it writes
is independently verifiable in the goal file, which is the whole point: "a goal emerged"
becomes a checkable fact rather than a narrated one.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

AGENTS = ("albedo", "john")
INTERVAL_S = 360          # check each agent this often
TENSION = 0.5             # minimum drive tension to consider emerging


def _check(agent: str) -> None:
    os.environ["OPENCLAW_AGENT"] = agent
    # import lazily AFTER setting the agent env, and re-resolve each cycle so paths follow
    import importlib
    import algorithms.goal_emergence as ge
    importlib.reload(ge)
    try:
        g = ge.maybe_emerge_goal(tension_threshold=TENSION, write=True)
    except Exception as e:                                   # never let one agent kill the loop
        print(f"[emergence] {agent}: error {e}", flush=True)
        return
    if g:
        print(f"[emergence] {agent}: goal emerged -> {g['content']!r} "
              f"(drive {g['drive']}, priority {g['priority']:.2f}, id {g['id']})", flush=True)


def main() -> None:
    print(f"[emergence] daemon up; agents={AGENTS} every {INTERVAL_S}s", flush=True)
    while True:
        for a in AGENTS:
            _check(a)
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
