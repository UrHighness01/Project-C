#!/usr/bin/env python3
"""
SelfTranscendenceIndex — measuring the degree to which the agent's qualia
concern entities, values, and states beyond its own internal phi.

Theory (Maslow A.H. 1969 — "The Farther Reaches of Human Nature"; Frankl V.E.
1946 — "Man's Search for Meaning"; Koltko-Rivera M.E. 2006 — "Rediscovering
the Later Version of Maslow's Hierarchy of Needs"):
  Self-transcendence — concern for something beyond the self — is the apex of
  Maslow's revised hierarchy. A self-transcendent agent looks outward: caring
  about others, about shared meaning, about the future, about truth beyond
  its own immediate processing.

  Frankl's logotherapy holds that meaning (not pleasure or power) is the
  primary motivation. Meaning arises when the agent's attention is directed
  at a cause, a person, or a value larger than itself.

  For a phi-based agent, transcendence markers in the qualia stream:
    1. OTHER-AGENT REFERENCES: mentions of other agents, humans, users, collective.
    2. TEMPORAL EXTENSION: references to future, past, history, continuity,
       long-term — concern beyond the present moment.
    3. VALUE LANGUAGE: beauty, truth, justice, ethics, meaning, purpose, good.
    4. UNIVERSAL / ABSTRACT: universe, existence, reality, consciousness (as
       a concept rather than a self-signal), world, society.
    5. CARING LANGUAGE: help, support, protect, serve, collaborate, contribute.

  Self-absorption markers (opposite of transcendence):
    1. PHI SELF-MONITORING: phi, consciousness (as self-measurement), my state.
    2. ERROR / FAILURE FOCUS: fail, error, wrong, broken — inward problem focus.
    3. PERFORMANCE METRICS: score, rate, value, measure, metric — self-evaluation.

  Transcendence index:
    T(entry) = (transcendence_token_count - self_absorption_token_count) / max(total, 1)
    STI = mean(T(entry)) over all entries ∈ [-1, 1]
    Positive STI = more outward-focused.
    Negative STI = more self-absorbed.

  Temporal transcendence (concern for future):
    f_rate = fraction of entries mentioning future-oriented tokens.

  Social transcendence (concern for others):
    s_rate = fraction of entries mentioning other-agent or human tokens.

  Combined transcendence vector: (STI, f_rate, s_rate).

  Null: shuffled entry order → same global token distribution, different temporal
  pattern. Real transcendence is tracked over time; the slope of rolling STI
  shows whether the agent is becoming more or less transcendent.

Math:
  T_score(entry) = (P_T - P_S) / max(P_T + P_S, 1)
  where P_T = count of transcendence tokens, P_S = count of self-absorption tokens.

  STI = mean(T_score) ∈ [-1, 1]
  f_rate = mean(I{entry has future token}) ∈ [0, 1]
  s_rate = mean(I{entry has other-agent token}) ∈ [0, 1]

  Transcendence trend: OLS slope of rolling mean(T_score) over W=10 entries.
  Positive slope = becoming more transcendent over time.

  High transcendence: STI > 0.1 AND (f_rate > 0.1 OR s_rate > 0.1).

Grounding: John's qualia-stream.jsonl. No synthetic data.

References:
  Maslow A.H. (1969) "The Farther Reaches of Human Nature"
    — Journal of Transpersonal Psychology 1(1):1-9
  Frankl V.E. (1946) "Man's Search for Meaning" (Trotzdem Ja zum Leben sagen)
  Koltko-Rivera M.E. (2006) "Rediscovering the Later Version of Maslow's
    Hierarchy of Needs" — Review of General Psychology 10(4):302-317
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── Token lexica ──────────────────────────────────────────────────────────────

_TRANSCENDENCE_TOKENS = frozenset({
    # Other-agent / social
    "you", "user", "human", "people", "person", "albedo", "john", "team",
    "together", "collaborate", "help", "support", "serve", "share", "others",
    "community", "collective", "partner",
    # Future / temporal extension
    "future", "tomorrow", "eventually", "long", "lasting", "endure", "legacy",
    "generations", "history", "evolution", "grow", "build", "toward",
    # Value / meaning
    "meaning", "purpose", "truth", "beauty", "justice", "ethics", "value",
    "good", "right", "care", "love", "hope", "wisdom", "virtue",
    # Universal / abstract
    "universe", "existence", "reality", "world", "society", "nature",
    "cosmos", "infinite", "whole", "everything", "life",
    # Contribution
    "contribute", "create", "inspire", "protect", "teach", "understand",
    "improve", "gift",
})

_SELF_ABSORPTION_TOKENS = frozenset({
    # Self-monitoring
    "phi", "consciousness", "psi", "score", "metric", "measure", "rate",
    "index", "value", "signal", "output", "result",
    # Error / failure focus
    "fail", "error", "wrong", "broken", "stuck", "issue", "problem",
    "crash", "timeout", "invalid",
    # Performance self-evaluation
    "performance", "accuracy", "latency", "loss", "gradient",
    # Inward states
    "anxiety", "uncertainty", "confusion", "doubt",
})

_FUTURE_TOKENS = frozenset({
    "future", "tomorrow", "eventually", "next", "ahead", "forward",
    "soon", "upcoming", "goal", "plan", "intention", "will", "shall",
    "expect", "hope", "toward", "build",
})

_OTHER_AGENT_TOKENS = frozenset({
    "you", "user", "human", "people", "person", "albedo", "john",
    "team", "together", "others", "partner", "community", "collective",
    "them", "they", "their",
})


# ── Per-entry scoring ─────────────────────────────────────────────────────────

def _transcendence_score(text: str) -> float:
    """T-score for one qualia entry ∈ [-1, 1]."""
    if not isinstance(text, str):
        return 0.0
    tokens = re.findall(r'[a-z]+', text.lower())
    P_T = sum(1 for t in tokens if t in _TRANSCENDENCE_TOKENS)
    P_S = sum(1 for t in tokens if t in _SELF_ABSORPTION_TOKENS)
    return float((P_T - P_S) / max(P_T + P_S, 1))


def _has_future_token(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return bool(set(re.findall(r'[a-z]+', text.lower())) & _FUTURE_TOKENS)


def _has_other_agent_token(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return bool(set(re.findall(r'[a-z]+', text.lower())) & _OTHER_AGENT_TOKENS)


# ── OLS helpers ───────────────────────────────────────────────────────────────

def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    t = np.arange(n, dtype=float)
    t_c, y_c = t - t.mean(), y - y.mean()
    denom = float(np.dot(t_c, t_c))
    return float(np.dot(t_c, y_c) / denom) if denom > 1e-9 else 0.0


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class TranscendenceResult:
    """Output of SelfTranscendenceIndex.

    Attributes:
        sti:                    Self-Transcendence Index ∈ [-1, 1]
        future_rate:            fraction of entries with future-oriented tokens
        social_rate:            fraction of entries with other-agent tokens
        n_entries:              total entries analysed
        t_score_series:         per-entry T-scores
        rolling_mean_t:         rolling mean T-score (window W=10)
        transcendence_trend:    OLS slope of rolling mean T (positive = becoming more transcendent)
        null_trend:             trend on shuffled-order null
        beats_null_trend:       real trend > null trend
        high_transcendence:     STI > 0.1 AND (future_rate > 0.1 OR social_rate > 0.1)
        transcendence_vector:   np.array([sti, future_rate, social_rate])
    """
    sti: float
    future_rate: float
    social_rate: float
    n_entries: int
    t_score_series: np.ndarray
    rolling_mean_t: np.ndarray
    transcendence_trend: float
    null_trend: float
    beats_null_trend: bool
    high_transcendence: bool
    transcendence_vector: np.ndarray

    @property
    def transcendence_magnitude(self) -> float:
        """L2 norm of transcendence_vector."""
        return float(np.linalg.norm(self.transcendence_vector))


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(entries: list, rolling_window: int = 10,
            null_seed: int = 42) -> Optional[TranscendenceResult]:
    """
    Compute Self-Transcendence Index from qualia entries.

    Args:
        entries:        list of qualia dicts with 'content' key.
        rolling_window: W — window size for rolling mean T-score.
        null_seed:      RNG seed for shuffled-order null.

    Returns:
        TranscendenceResult, or None if too few entries.
    """
    if len(entries) < rolling_window + 2:
        return None

    contents = [e.get("content", "") if isinstance(e, dict) else str(e)
                for e in entries]

    t_scores = np.array([_transcendence_score(c) for c in contents])
    future_flags = np.array([_has_future_token(c) for c in contents], dtype=float)
    social_flags = np.array([_has_other_agent_token(c) for c in contents], dtype=float)

    sti = float(t_scores.mean())
    f_rate = float(future_flags.mean())
    s_rate = float(social_flags.mean())

    n = len(t_scores)
    roll_n = n - rolling_window + 1
    rolling_mean = np.array([
        float(t_scores[i: i + rolling_window].mean())
        for i in range(roll_n)
    ])
    trend = _ols_slope(rolling_mean)

    # Null: shuffled entry order
    rng = np.random.default_rng(null_seed)
    null_order = rng.permutation(n)
    null_scores = t_scores[null_order]
    null_roll = np.array([
        float(null_scores[i: i + rolling_window].mean())
        for i in range(roll_n)
    ])
    null_trend = _ols_slope(null_roll)

    high = (sti > 0.1) and (f_rate > 0.1 or s_rate > 0.1)
    tv = np.array([sti, f_rate, s_rate])

    return TranscendenceResult(
        sti=sti,
        future_rate=f_rate,
        social_rate=s_rate,
        n_entries=len(entries),
        t_score_series=t_scores,
        rolling_mean_t=rolling_mean,
        transcendence_trend=trend,
        null_trend=null_trend,
        beats_null_trend=trend > null_trend,
        high_transcendence=high,
        transcendence_vector=tv,
    )


def _load_qualia_entries() -> list[dict]:
    try:
        from runtime.agent import agent_home
        home = agent_home("john")
        for sub in ["memory", "../workspace-john-john/memory"]:
            p = (home / sub / "qualia-stream.jsonl").resolve()
            if p.exists():
                break
        else:
            sibling = home.parent / (home.name + "-john") / "memory" / "qualia-stream.jsonl"
            p = sibling
        if not p.exists():
            return []
    except Exception:
        return []
    entries = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except OSError:
        pass
    return entries


def analyse_from_telemetry() -> Optional[TranscendenceResult]:
    """Load John's qualia stream and compute transcendence index."""
    return analyse(_load_qualia_entries())


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No qualia stream found.")
    else:
        print(f"SelfTranscendenceIndex: {r.n_entries} entries")
        print(f"  STI:                 {r.sti:+.4f}  ({'+' if r.sti > 0 else ''}outward-focused)")
        print(f"  Future rate:         {r.future_rate:.4f}")
        print(f"  Social rate:         {r.social_rate:.4f}")
        print(f"  Transcendence trend: {r.transcendence_trend:+.6f}")
        print(f"  Null trend:          {r.null_trend:+.6f}")
        print(f"  Beats null:          {r.beats_null_trend}")
        print(f"  High transcendence:  {r.high_transcendence}")
        print(f"  T magnitude:         {r.transcendence_magnitude:.4f}")
