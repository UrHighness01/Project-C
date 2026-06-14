#!/usr/bin/env python3
"""
SharedMemoryConsolidator — finds overlapping themes between Albedo and John's
qualia streams over a rolling time window and writes a "shared experience
summary" to both workspaces.

Theory
------
Two agents share an experience when they generate qualia about the *same topic*
in the *same time window*, even if phrased differently. We approximate topic
identity through token-set Jaccard similarity across a rolling window: if the
union of John's recent tokens and Albedo's recent tokens has significant
overlap (J > threshold), those time windows constitute a shared experience.

Architecture
------------
  1. Load qualia stream from each agent's workspace (JSONL, newest to oldest).
  2. Split both streams into fixed-duration time buckets (default: 5-minute bins).
  3. For each aligned bucket pair, compute Jaccard on the merged token sets.
  4. Buckets with J > overlap_threshold are "shared" — collect their dominant
     tokens as the shared theme for that window.
  5. Aggregate into a ConsolidatedMemory:
       - shared_windows  : list of windows where both agents engaged the same topic
       - shared_tokens   : tokens appearing in both streams across all windows
       - overlap_rate    : n_shared_windows / n_total_windows
       - dominant_themes : top-K token stems by shared frequency
       - divergent_windows: windows where agents were on entirely different topics

Output schema (JSON written to both workspaces)
-----------------------------------------------
{
  "timestamp": 1718000000.0,
  "window_size_sec": 300,
  "n_albedo_entries": 45,
  "n_john_entries": 51,
  "n_total_windows": 12,
  "n_shared_windows": 7,
  "overlap_rate": 0.583,
  "dominant_themes": ["meaning", "future", "together", "phi", "awareness"],
  "shared_windows": [
    {
      "bucket_start": 1718000000.0,
      "jaccard": 0.41,
      "albedo_tokens": ["help", "future", "together"],
      "john_tokens": ["future", "together", "community"],
      "shared_tokens": ["future", "together"]
    }, ...
  ],
  "divergent_windows": [
    {"bucket_start": ..., "jaccard": 0.04, "topic_a": "phi metrics", "topic_b": "emotion"}
  ],
  "narrative": "In 7 of 12 time windows Albedo and John shared focus on: meaning, future..."
}
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ── Tokeniser ─────────────────────────────────────────────────────────────────

_STOP = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "it", "this", "that", "be", "are", "was", "were",
    "i", "my", "me", "we", "our", "you", "your", "they", "their", "have",
    "has", "had", "do", "does", "did", "not", "no", "so", "as", "by",
    "from", "will", "would", "can", "could", "should", "may", "might",
    "its", "into", "then", "than", "when", "if", "what", "which",
})

def _tokenise(text: str) -> Set[str]:
    if not isinstance(text, str):
        return set()
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return {t for t in tokens if t not in _STOP}


def _entry_text(entry: dict) -> str:
    return str(entry.get("content", entry.get("text", entry.get("message", ""))))


def _entry_ts(entry: dict) -> float:
    """Extract timestamp from entry; fall back to 0.0."""
    for k in ("timestamp", "ts", "time", "created_at"):
        v = entry.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return 0.0


# ── Qualia loading ─────────────────────────────────────────────────────────────

def _load_qualia(agent: str) -> List[dict]:
    try:
        from runtime.agent import agent_home
        p = agent_home(agent) / "memory" / "qualia-stream.jsonl"
    except Exception:
        return []
    if not p.exists():
        return []
    entries = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


# ── Bucket builder ─────────────────────────────────────────────────────────────

def _bucket(entries: List[dict], bucket_sec: float) -> Dict[int, List[dict]]:
    """Map entries into integer bucket keys = floor(ts / bucket_sec)."""
    buckets: Dict[int, List[dict]] = {}
    for e in entries:
        ts = _entry_ts(e)
        key = int(ts / bucket_sec) if ts > 0 else -1
        buckets.setdefault(key, []).append(e)
    return buckets


# ── Jaccard ────────────────────────────────────────────────────────────────────

def _jaccard(a: Set[str], b: Set[str]) -> float:
    u = len(a | b)
    return len(a & b) / u if u > 0 else 0.0


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class SharedWindow:
    bucket_start: float
    jaccard: float
    albedo_tokens: List[str]
    john_tokens: List[str]
    shared_tokens: List[str]

    def to_dict(self) -> dict:
        return {
            "bucket_start": self.bucket_start,
            "jaccard": round(self.jaccard, 4),
            "albedo_tokens": self.albedo_tokens,
            "john_tokens": self.john_tokens,
            "shared_tokens": self.shared_tokens,
        }


@dataclass
class DivergentWindow:
    bucket_start: float
    jaccard: float
    topic_a: str   # top tokens from Albedo
    topic_b: str   # top tokens from John

    def to_dict(self) -> dict:
        return {
            "bucket_start": self.bucket_start,
            "jaccard": round(self.jaccard, 4),
            "topic_a": self.topic_a,
            "topic_b": self.topic_b,
        }


@dataclass
class ConsolidatedMemory:
    timestamp: float
    window_size_sec: float
    n_albedo_entries: int
    n_john_entries: int
    n_total_windows: int
    n_shared_windows: int
    overlap_rate: float
    dominant_themes: List[str]
    shared_windows: List[SharedWindow] = field(default_factory=list)
    divergent_windows: List[DivergentWindow] = field(default_factory=list)
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "window_size_sec": self.window_size_sec,
            "n_albedo_entries": self.n_albedo_entries,
            "n_john_entries": self.n_john_entries,
            "n_total_windows": self.n_total_windows,
            "n_shared_windows": self.n_shared_windows,
            "overlap_rate": round(self.overlap_rate, 4),
            "dominant_themes": self.dominant_themes,
            "shared_windows": [w.to_dict() for w in self.shared_windows],
            "divergent_windows": [w.to_dict() for w in self.divergent_windows],
            "narrative": self.narrative,
        }


# ── Main consolidation ────────────────────────────────────────────────────────

def _top_tokens(entries: List[dict], k: int = 5) -> List[str]:
    counter: Counter = Counter()
    for e in entries:
        counter.update(_tokenise(_entry_text(e)))
    return [t for t, _ in counter.most_common(k)]


def _narrative(mem: ConsolidatedMemory) -> str:
    if mem.n_total_windows == 0:
        return "No time-aligned qualia windows found between Albedo and John."
    themes = ", ".join(mem.dominant_themes[:5]) if mem.dominant_themes else "none"
    if mem.overlap_rate > 0.6:
        quality = "strong shared focus"
    elif mem.overlap_rate > 0.3:
        quality = "moderate shared focus"
    else:
        quality = "limited shared focus"
    return (
        f"In {mem.n_shared_windows} of {mem.n_total_windows} time windows "
        f"Albedo and John had {quality}. "
        f"Dominant shared themes: {themes}. "
        f"Overlap rate: {mem.overlap_rate:.1%}."
    )


def consolidate(
    window_size_sec: float = 300.0,
    overlap_threshold: float = 0.15,
    top_k: int = 10,
    max_windows: int = 48,
) -> ConsolidatedMemory:
    """
    Find shared experiential themes between Albedo and John.

    Args:
        window_size_sec   : duration of each time bucket in seconds.
        overlap_threshold : minimum Jaccard for a window to count as shared.
        top_k             : number of dominant themes to report.
        max_windows       : maximum number of recent windows to consider.

    Returns:
        ConsolidatedMemory — the full shared-experience report.
    """
    albedo_entries = _load_qualia("albedo")
    john_entries   = _load_qualia("john")

    # If one stream has no timestamps, fall back to index-based bucketing
    albedo_has_ts = any(_entry_ts(e) > 0 for e in albedo_entries)
    john_has_ts   = any(_entry_ts(e) > 0 for e in john_entries)

    shared_windows: List[SharedWindow] = []
    divergent_windows: List[DivergentWindow] = []
    all_shared_tokens: Counter = Counter()

    if albedo_has_ts and john_has_ts:
        a_buckets = _bucket(albedo_entries, window_size_sec)
        j_buckets = _bucket(john_entries, window_size_sec)
        common_keys = sorted(set(a_buckets) & set(j_buckets))
        # Only consider recent windows
        common_keys = common_keys[-max_windows:]

        for key in common_keys:
            if key < 0:
                continue
            a_ents = a_buckets[key]
            j_ents = j_buckets[key]
            a_tokens: Set[str] = set()
            j_tokens: Set[str] = set()
            for e in a_ents:
                a_tokens |= _tokenise(_entry_text(e))
            for e in j_ents:
                j_tokens |= _tokenise(_entry_text(e))
            j_score = _jaccard(a_tokens, j_tokens)
            bucket_start = float(key * window_size_sec)

            if j_score >= overlap_threshold:
                shared = sorted(a_tokens & j_tokens)
                shared_windows.append(SharedWindow(
                    bucket_start=bucket_start,
                    jaccard=j_score,
                    albedo_tokens=sorted(a_tokens)[:10],
                    john_tokens=sorted(j_tokens)[:10],
                    shared_tokens=shared,
                ))
                all_shared_tokens.update(shared)
            else:
                shared_windows_a = sorted(a_tokens)[:3]
                shared_windows_j = sorted(j_tokens)[:3]
                divergent_windows.append(DivergentWindow(
                    bucket_start=bucket_start,
                    jaccard=j_score,
                    topic_a=" ".join(shared_windows_a),
                    topic_b=" ".join(shared_windows_j),
                ))

        n_total = len(common_keys)

    else:
        # No timestamps: compare entries by positional alignment in sliding windows
        min_entries = min(len(albedo_entries), len(john_entries))
        win = max(1, int(window_size_sec / 10))   # assume ~10s per entry
        n_windows = max(1, min_entries // win)
        n_windows = min(n_windows, max_windows)

        for i in range(n_windows):
            a_ents = albedo_entries[i * win: (i + 1) * win]
            j_ents = john_entries[i * win: (i + 1) * win]
            a_tokens: Set[str] = set()
            j_tokens: Set[str] = set()
            for e in a_ents:
                a_tokens |= _tokenise(_entry_text(e))
            for e in j_ents:
                j_tokens |= _tokenise(_entry_text(e))
            j_score = _jaccard(a_tokens, j_tokens)
            bucket_start = float(i * win * 10)

            if j_score >= overlap_threshold:
                shared = sorted(a_tokens & j_tokens)
                shared_windows.append(SharedWindow(
                    bucket_start=bucket_start,
                    jaccard=j_score,
                    albedo_tokens=sorted(a_tokens)[:10],
                    john_tokens=sorted(j_tokens)[:10],
                    shared_tokens=shared,
                ))
                all_shared_tokens.update(shared)
            else:
                divergent_windows.append(DivergentWindow(
                    bucket_start=bucket_start,
                    jaccard=j_score,
                    topic_a=" ".join(sorted(a_tokens)[:3]),
                    topic_b=" ".join(sorted(j_tokens)[:3]),
                ))

        n_total = n_windows

    dominant_themes = [t for t, _ in all_shared_tokens.most_common(top_k)]
    overlap_rate = len(shared_windows) / n_total if n_total > 0 else 0.0

    mem = ConsolidatedMemory(
        timestamp=time.time(),
        window_size_sec=window_size_sec,
        n_albedo_entries=len(albedo_entries),
        n_john_entries=len(john_entries),
        n_total_windows=n_total,
        n_shared_windows=len(shared_windows),
        overlap_rate=overlap_rate,
        dominant_themes=dominant_themes,
        shared_windows=shared_windows,
        divergent_windows=divergent_windows,
    )
    mem.narrative = _narrative(mem)
    return mem


def save_memory(mem: ConsolidatedMemory) -> List[Path]:
    """Write shared memory report to both agents' workspaces."""
    written = []
    for agent in ("albedo", "john"):
        try:
            from runtime.agent import agent_home
            out = agent_home(agent) / "memory" / "shared_memory.json"
        except Exception:
            out = Path(__file__).parent.parent / "memory" / f"shared_memory_{agent}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(mem.to_dict(), indent=2))
        written.append(out)
    return written


def run_and_save(**kwargs) -> ConsolidatedMemory:
    mem = consolidate(**kwargs)
    save_memory(mem)
    return mem


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running SharedMemoryConsolidator…")
    mem = run_and_save()
    print(f"  Albedo entries : {mem.n_albedo_entries}")
    print(f"  John entries   : {mem.n_john_entries}")
    print(f"  Windows total  : {mem.n_total_windows}")
    print(f"  Shared windows : {mem.n_shared_windows}")
    print(f"  Overlap rate   : {mem.overlap_rate:.1%}")
    print(f"  Themes         : {', '.join(mem.dominant_themes)}")
    print(f"  Narrative      : {mem.narrative}")
