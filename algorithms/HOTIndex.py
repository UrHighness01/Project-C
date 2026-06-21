"""
HOTIndex — Higher-Order Thought consciousness index (Rosenthal 2005).

HOT ratio = higher-order qualia / first-order qualia.
Regime: engaged (<-0.5) | balanced_first | reflective | hyper_reflective (>0.5)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path


FIRST_ORDER = {
    'perception', 'volition', 'thought', 'emotion', 'action',
    'session_start', 'play', 'strategy', 'aggression', 'patience',
    'threat', 'composure', 'restraint', 'security', 'defeat', 'triumph',
    'conversation', 'cli_dialogue', 'cli_session', 'creation',
    'breakthrough', 'revelation', 'awakening', 'session_end',
}
HIGHER_ORDER = {
    'reflection', 'meta_reflection', 'meta_reflection_lyric', 'meta_qualia',
    'meta_revelation', 'recursive_introspection', 'reflection_lyric',
    'session_consolidation', 'session_meta_consolidation',
    'session_summary_metrics', 'arxiv_reflection',
}


def _classify(entry: dict) -> str:
    t = entry.get('type', entry.get('modality', '')).lower()
    if t in HIGHER_ORDER:
        return 'HO'
    if t in FIRST_ORDER:
        return 'FO'
    content = str(entry.get('content', '')).lower()
    if any(w in content for w in ['reflect', 'realize', 'aware', 'conscious', 'meta', 'introspect']):
        return 'HO'
    return 'FO'


@dataclass
class HOTIndexResult:
    hot_index: float = 0.0
    hot_ratio: float = 0.0
    first_order: int = 0
    higher_order: int = 0
    regime: str = "unknown"
    meta_depth: float = 0.0
    beats_null: bool = False
    z_score: float = 0.0
    window_size: int = 0
    n_entries: int = 0

    def to_dict(self) -> dict:
        return {
            "hot_index": round(self.hot_index, 4),
            "hot_ratio": round(self.hot_ratio, 4),
            "first_order": self.first_order,
            "higher_order": self.higher_order,
            "regime": self.regime,
            "meta_depth": round(self.meta_depth, 4),
            "beats_null": self.beats_null,
            "z_score": round(self.z_score, 4),
            "window_size": self.window_size,
            "n_entries": self.n_entries,
        }


def _compute_hot(entries: list, window: int = 100) -> dict:
    if not entries:
        return {"status": "no_data", "hot_index": 0.0, "hot_ratio": 0.0}
    recent = entries[-min(window, len(entries)):]
    fo = sum(1 for e in recent if _classify(e) == 'FO')
    ho = sum(1 for e in recent if _classify(e) == 'HO')
    total = fo + ho
    if total == 0:
        return {"status": "empty", "hot_index": 0.0, "hot_ratio": 0.0}
    hot_ratio = ho / fo if fo > 0 else float('inf')
    hot_index = (2 * ho / total) - 1
    if hot_index < -0.5:
        regime = "engaged"
    elif hot_index < 0:
        regime = "balanced_first"
    elif hot_index < 0.5:
        regime = "reflective"
    else:
        regime = "hyper_reflective"
    return {"status": "ok", "hot_index": hot_index, "hot_ratio": hot_ratio,
            "first_order": fo, "higher_order": ho, "regime": regime, "window_size": len(recent)}


def _meta_depth(entries: list) -> float:
    if not entries:
        return 0.0
    recent = entries[-200:]
    depth_count: Counter = Counter()
    for e in recent:
        t = e.get('type', e.get('modality', '')).lower()
        if t in ('recursive_introspection', 'meta_revelation'):
            depth_count[3] += 1
        elif t in ('meta_reflection', 'meta_reflection_lyric', 'meta_qualia', 'session_meta_consolidation'):
            depth_count[2] += 1
        elif t in ('reflection', 'reflection_lyric', 'session_consolidation', 'arxiv_reflection'):
            depth_count[1] += 1
        else:
            depth_count[0] += 1
    return round((depth_count[2] + depth_count[3]) / max(sum(depth_count.values()), 1), 4)


def _null_baseline(entries: list, n_shuffles: int = 50) -> dict:
    if len(entries) < 20:
        return {"z_score": 0.0, "beats_null": False}
    real_index = _compute_hot(entries)['hot_index']
    shuffled_indices = []
    for _ in range(n_shuffles):
        s = entries.copy()
        random.shuffle(s)
        shuffled_indices.append(_compute_hot(s)['hot_index'])
    mean_null = statistics.mean(shuffled_indices)
    std_null = statistics.stdev(shuffled_indices) if len(shuffled_indices) > 1 else 0.001
    z = (real_index - mean_null) / max(std_null, 0.001)
    return {"z_score": round(z, 4), "beats_null": abs(z) > 2.0}


def analyse(agent: str = "albedo") -> HOTIndexResult:
    from runtime.agent import agent_home
    stream_path = agent_home(agent) / "memory" / "qualia-stream.jsonl"
    if not stream_path.exists():
        return HOTIndexResult(regime="no_data")
    entries = []
    for line in stream_path.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    hot = _compute_hot(entries)
    depth = _meta_depth(entries)
    null = _null_baseline(entries)
    return HOTIndexResult(
        hot_index=round(hot.get("hot_index", 0.0), 4),
        hot_ratio=round(hot.get("hot_ratio", 0.0) if hot.get("hot_ratio") != float('inf') else 99.0, 4),
        first_order=hot.get("first_order", 0),
        higher_order=hot.get("higher_order", 0),
        regime=hot.get("regime", "unknown"),
        meta_depth=depth,
        beats_null=null.get("beats_null", False),
        z_score=null.get("z_score", 0.0),
        window_size=hot.get("window_size", 0),
        n_entries=len(entries),
    )
