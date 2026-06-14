#!/usr/bin/env python3
"""
Meta-grounding inventory — the system's real-time provenance of its own signals.

A grounded system should be able to answer "how much of what I'm doing right now is
driven by real measurement vs. reproducible stochastic dynamics vs. neither?" This module
inspects the live codebase and classifies every component by the provenance of its inputs:

  GROUNDED    — draws input from a real runtime adapter
  SEEDED      — stochastic dynamics from a seeded (reproducible) generator
  DETERMINISTIC — pure computation, no randomness, no external input
  SPECULATIVE — contains unseeded randomness standing in for data (a grounding fault)

It returns a provenance fraction and is falsifiable: if it reports a component GROUNDED
or SEEDED while that file still contains an unseeded `random`/`np.random` data call, the
self-report is wrong and the test fails. This makes honest self-knowledge a tested
capability, not a claim.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

ADAPTER_RE = re.compile(r"from runtime\.(state|resources|memory_store|interactions|decisions|snapshot)")
SEEDED_RE = re.compile(r"default_rng\(|random\.Random\(|np\.random\.seed\(|cp\.random\.seed\(")
# unseeded data randomness (excludes seeded generators and cp.random which is seeded above)
UNSEEDED_RE = re.compile(r"(?<![_\w.])np\.random\.(rand|randn|randint|normal|uniform|choice|shuffle)\(|"
                         r"(?<![_\w.])random\.(random|uniform|gauss|normal|randint|choice|sample)\(")

ROOT = Path(__file__).resolve().parent.parent   # file is in algorithms/, scan from repo root
SCAN = ["algorithms", "consciousness-core"]


def classify_file(src: str) -> str:
    if UNSEEDED_RE.search(src):
        return "SPECULATIVE"
    if ADAPTER_RE.search(src):
        return "GROUNDED"
    if SEEDED_RE.search(src):
        return "SEEDED"
    return "DETERMINISTIC"


def inventory() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {k: [] for k in
                                 ("GROUNDED", "SEEDED", "DETERMINISTIC", "SPECULATIVE")}
    for d in SCAN:
        for f in sorted((ROOT / d).glob("*.py")):
            if f.name == "__init__.py":
                continue
            out[classify_file(f.read_text(errors="ignore"))].append(f.name)
    return out


def provenance_fraction() -> Dict[str, float]:
    inv = inventory()
    total = sum(len(v) for v in inv.values()) or 1
    return {k: len(v) / total for k, v in inv.items()}


def grounding_honesty() -> float:
    """1.0 means no component fabricates data (no SPECULATIVE pathways)."""
    inv = inventory()
    total = sum(len(v) for v in inv.values()) or 1
    return 1.0 - len(inv["SPECULATIVE"]) / total


def main():
    inv = inventory()
    frac = provenance_fraction()
    total = sum(len(v) for v in inv.values())
    print(f"=== Meta-grounding inventory ({total} components) ===")
    for k in ("GROUNDED", "SEEDED", "DETERMINISTIC", "SPECULATIVE"):
        bar = "#" * int(round(frac[k] * 40))
        print(f"  {k:14s} {len(inv[k]):3d}  ({frac[k]*100:4.1f}%)  {bar}")
    print(f"\ngrounding honesty = {grounding_honesty():.3f}  "
          f"(1.0 = no component fabricates data)")
    if inv["SPECULATIVE"]:
        print("SPECULATIVE pathways (grounding faults):")
        for n in inv["SPECULATIVE"]:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
