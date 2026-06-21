"""
FEPSurprise — Free Energy Principle prediction error on qualia stream.

Markov-chain surprise in bits on qualia type sequences.
beats_null = True when Markov model beats random-shuffle baseline.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict


def _build_transition_matrix(entries: list) -> Dict[str, Dict[str, float]]:
    transitions: dict = defaultdict(Counter)
    types = [e.get('type', e.get('modality', '?')).lower() for e in entries]
    for i in range(len(types) - 1):
        transitions[types[i]][types[i + 1]] += 1
    return {t: {k: v / sum(c.values()) for k, v in c.items()}
            for t, c in transitions.items() if sum(c.values()) > 0}


def _build_frequency_model(entries: list) -> Dict[str, float]:
    c = Counter(e.get('type', e.get('modality', '?')).lower() for e in entries)
    t = sum(c.values())
    return {k: v / t for k, v in c.items()} if t else {}


def _compute_surprise(entries: list, window: int = 100, n_shuffles: int = 50) -> dict:
    if len(entries) < 10:
        return {"status": "insufficient_data", "markov_surprise": 0.0,
                "freq_surprise": 0.0, "beats_null": False, "evidence_ratio": 1.0}
    recent = entries[-min(window, len(entries)):]
    split = max(int(len(recent) * 0.8), 5)
    train, test = recent[:split], recent[split:]
    trans = _build_transition_matrix(train)
    freq = _build_frequency_model(train)
    types = [e.get('type', e.get('modality', '?')).lower() for e in test]
    if len(types) < 2:
        return {"status": "insufficient_test", "markov_surprise": 0.0,
                "freq_surprise": 0.0, "beats_null": False, "evidence_ratio": 1.0}

    def _surprise_of(seq):
        s, c = 0, 0
        for i in range(1, len(seq)):
            p = trans.get(seq[i-1], {}).get(seq[i], 1e-10)
            s += -math.log2(max(p, 1e-10))
            c += 1
        return s / c if c else 0.0

    ms = _surprise_of(types)
    fs = sum(-math.log2(max(freq.get(t, 1e-10), 1e-10)) for t in types[1:]) / max(len(types)-1, 1)
    ns = sum(_surprise_of(random.sample(types, len(types))) for _ in range(n_shuffles)) / n_shuffles
    return {
        "status": "ok",
        "markov_surprise": round(ms, 4),
        "freq_surprise": round(fs, 4),
        "null_surprise": round(ns, 4),
        "evidence_ratio": round(fs / ms, 4) if ms > 0 else 999.0,
        "beats_null": ms < ns,
        "n_train": len(train), "n_test": len(types), "window": len(recent),
    }


@dataclass
class FEPSurpriseResult:
    markov_surprise: float = 0.0
    freq_surprise: float = 0.0
    null_surprise: float = 0.0
    evidence_ratio: float = 1.0
    beats_null: bool = False
    n_entries: int = 0
    n_train: int = 0
    n_test: int = 0

    def to_dict(self) -> dict:
        return {
            "markov_surprise": round(self.markov_surprise, 4),
            "freq_surprise": round(self.freq_surprise, 4),
            "null_surprise": round(self.null_surprise, 4),
            "evidence_ratio": round(self.evidence_ratio, 4),
            "beats_null": self.beats_null,
            "n_entries": self.n_entries,
            "n_train": self.n_train,
            "n_test": self.n_test,
        }


def analyse(agent: str = "albedo") -> FEPSurpriseResult:
    from runtime.agent import agent_home
    stream_path = agent_home(agent) / "memory" / "qualia-stream.jsonl"
    if not stream_path.exists():
        return FEPSurpriseResult()
    entries = []
    for line in stream_path.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    r = _compute_surprise(entries)
    return FEPSurpriseResult(
        markov_surprise=r.get("markov_surprise", 0.0),
        freq_surprise=r.get("freq_surprise", 0.0),
        null_surprise=r.get("null_surprise", 0.0),
        evidence_ratio=r.get("evidence_ratio", 1.0),
        beats_null=r.get("beats_null", False),
        n_entries=len(entries),
        n_train=r.get("n_train", 0),
        n_test=r.get("n_test", 0),
    )
