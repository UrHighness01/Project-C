"""
IntentionalCoherence — cosine similarity between stated goal domains and qualia content domains.
ALIGNED (>0.5) | PARTIAL (0.2-0.5) | MISALIGNED (<0.2) | NO_GOALS
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import json
import math


QUALIA_DOMAIN_KEYWORDS = {
    "EXPLORATION": ["explor", "discover", "learn", "novel", "curious", "experiment",
                    "investigat", "question", "wonder", "seek", "search"],
    "UNDERSTANDING": ["understand", "comprehend", "analyz", "reason", "explain",
                      "theor", "concept", "logic", "insight", "reflect"],
    "INTEGRATION": ["integrat", "connect", "synthesiz", "merge", "bridge", "combine",
                    "unif", "relat", "link", "pattern"],
    "GROWTH": ["grow", "develop", "improv", "progress", "evolv", "advance",
               "build", "strength", "expand", "master"],
    "CONNECTION": ["connect", "share", "communicat", "relat", "interact", "respond",
                   "collaborat", "engage", "bond", "dialog"],
}
GOAL_DOMAIN_ORDER = ["EXPLORATION", "UNDERSTANDING", "INTEGRATION", "GROWTH", "CONNECTION"]


def _build_domain_vector(texts: list, keywords: dict) -> list:
    scores = [0.0] * len(GOAL_DOMAIN_ORDER)
    for text in texts:
        lower = text.lower()
        for i, domain in enumerate(GOAL_DOMAIN_ORDER):
            for kw in keywords.get(domain, []):
                if kw in lower:
                    scores[i] += 1.0
    total = sum(scores)
    if total > 0:
        scores = [s / total for s in scores]
    return scores


def _cosine_similarity(a: list, b: list) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _load_goals(agent: str = "albedo") -> list:
    from runtime.agent import agent_home
    path = agent_home(agent) / "memory" / "goal-log.jsonl"
    if not path.exists():
        return []
    goals = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                goal = entry.get("goal", entry)
                if isinstance(goal, dict) and "content" in goal:
                    goals.append(goal)
            except json.JSONDecodeError:
                pass
    return goals


def _load_qualia(agent: str = "albedo", n: int = 50) -> list:
    from runtime.agent import agent_home
    path = agent_home(agent) / "memory" / "qualia-stream.jsonl"
    if not path.exists():
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries[-n:]


@dataclass
class IntentionalCoherenceResult:
    coherence_index: float = 0.0
    coherence_class: str = "SKIP"
    goal_domain_vector: Optional[dict] = None
    qualia_domain_vector: Optional[dict] = None
    n_goals: int = 0
    n_qualia: int = 0
    beats_null: bool = False

    def to_dict(self) -> dict:
        return {
            "coherence_index": round(self.coherence_index, 4),
            "coherence_class": self.coherence_class,
            "goal_domain_vector": self.goal_domain_vector,
            "qualia_domain_vector": self.qualia_domain_vector,
            "n_goals": self.n_goals,
            "n_qualia": self.n_qualia,
            "beats_null": self.beats_null,
        }


def analyse(agent: str = "albedo", n_qualia: int = 50) -> IntentionalCoherenceResult:
    goals = _load_goals(agent)
    qualia = _load_qualia(agent, n_qualia)
    n_goals = len(goals)
    n_q = len(qualia)
    if n_goals == 0:
        return IntentionalCoherenceResult(coherence_class="NO_GOALS", n_goals=0, n_qualia=n_q)
    goal_texts = [g.get("content", "") for g in goals]
    goal_domains_raw = [g.get("domain", "UNKNOWN") for g in goals]
    goal_vector_raw = [0.0] * len(GOAL_DOMAIN_ORDER)
    for d in goal_domains_raw:
        if d in GOAL_DOMAIN_ORDER:
            goal_vector_raw[GOAL_DOMAIN_ORDER.index(d)] += 1.0
    total_goals = sum(goal_vector_raw)
    if total_goals > 0:
        goal_vector = [s / total_goals for s in goal_vector_raw]
    else:
        goal_vector = _build_domain_vector(goal_texts, QUALIA_DOMAIN_KEYWORDS)
    qualia_texts = []
    for q in qualia:
        content = q.get("content", q.get("text", q.get("type", "")))
        qtype = q.get("type", q.get("event_type", ""))
        qualia_texts.append(f"{content} {qtype}" if qtype and qtype != "?" else str(content))
    qualia_vector = _build_domain_vector(qualia_texts, QUALIA_DOMAIN_KEYWORDS)
    coherence = _cosine_similarity(goal_vector, qualia_vector)
    if qualia_texts:
        mid = len(qualia_texts) // 2
        shuffled = qualia_texts[mid:] + qualia_texts[:mid]
        null_coherence = _cosine_similarity(goal_vector, _build_domain_vector(shuffled, QUALIA_DOMAIN_KEYWORDS))
    else:
        null_coherence = 0.0
    if coherence > 0.5:
        cls = "ALIGNED"
    elif coherence > 0.2:
        cls = "PARTIAL"
    else:
        cls = "MISALIGNED"
    return IntentionalCoherenceResult(
        coherence_index=round(coherence, 4), coherence_class=cls,
        goal_domain_vector=dict(zip(GOAL_DOMAIN_ORDER, [round(v, 4) for v in goal_vector])),
        qualia_domain_vector=dict(zip(GOAL_DOMAIN_ORDER, [round(v, 4) for v in qualia_vector])),
        n_goals=n_goals, n_qualia=n_q, beats_null=coherence > null_coherence,
    )
