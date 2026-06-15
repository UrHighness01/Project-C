#!/usr/bin/env python3
"""
AttentionFocusNarrower — surface the K most information-dense moments in the
current qualia stream so the agent can direct cognitive resources efficiently.

Theory
------
Information-dense moments are local entropy peaks: windows where the probability
distribution over qualia tokens is most concentrated and least predictable from
surroundings. We operationalise this with two complementary measures:

  1. Local Shannon entropy (window entropy)
     H(w) = -sum_i p_i * log2(p_i) over the token frequency distribution
     inside a sliding window w. A short window with high entropy = many
     distinct tokens = content-rich.

  2. Surprisal relative to context
     For each window w at position t, compute KL divergence from the
     running background distribution P_bg (all tokens seen so far):
       KL(P_w || P_bg) = sum_i P_w(i) * log(P_w(i) / P_bg(i))
     High KL = the window is surprising relative to the agent's experience
     so far = a candidate focus point.

  Combined score: score(w) = alpha * H(w) + (1 - alpha) * KL(w)
  where alpha=0.5 weights local richness vs. relative surprise equally.

  Top-K non-overlapping windows are returned as FocusPoint objects, ranked
  by score descending.  Overlap suppression: a window is eligible only if
  its centre is at least `window_size` samples away from all already-selected
  centres (greedy NMS).

Output
------
FocusNarrowerResult:
  top_k           : List[FocusPoint]    -- ranked best windows to attend to
  background_entropy : float            -- H of the full stream (baseline)
  mean_score      : float               -- mean score across all windows
  focus_ratio     : float               -- top-k mean score / background_entropy
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional


# ── Token extraction ──────────────────────────────────────────────────────────

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "it", "its", "i", "me", "my", "we", "our", "you", "your", "he", "she",
    "they", "their", "in", "on", "at", "to", "of", "for", "with", "that",
    "this", "be", "have", "has", "had", "do", "did", "so", "as",
})


def _tokenise(text: str) -> List[str]:
    import re
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]


def _to_token_stream(entries: List[dict]) -> List[str]:
    tokens: List[str] = []
    for e in entries:
        text = e.get("content", e.get("text", ""))
        if isinstance(text, str):
            tokens.extend(_tokenise(text))
    return tokens


# ── Entropy / KL helpers ──────────────────────────────────────────────────────

def _entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return float(sum(
        -v / total * math.log2(v / total)
        for v in counts.values()
        if v > 0
    ))


def _kl_div(local: Counter, background: Counter) -> float:
    bg_total = sum(background.values()) or 1
    lo_total = sum(local.values()) or 1
    kl = 0.0
    for tok, lc in local.items():
        p = lc / lo_total
        q = background.get(tok, 0) / bg_total
        if q <= 0:
            q = 1e-9
        kl += p * math.log(p / q)
    return max(0.0, kl)


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class FocusPoint:
    rank: int
    start_idx: int
    end_idx: int
    window_tokens: List[str]
    local_entropy: float
    surprisal_kl: float
    score: float
    top_tokens: List[str]        # top-5 tokens by frequency in this window


@dataclass
class FocusNarrowerResult:
    top_k: List[FocusPoint] = field(default_factory=list)
    background_entropy: float = 0.0
    mean_score: float = 0.0
    focus_ratio: float = 0.0

    def to_dict(self) -> dict:
        return {
            "background_entropy": round(self.background_entropy, 4),
            "mean_score": round(self.mean_score, 4),
            "focus_ratio": round(self.focus_ratio, 4),
            "top_k": [
                {
                    "rank": fp.rank,
                    "start_idx": fp.start_idx,
                    "end_idx": fp.end_idx,
                    "local_entropy": round(fp.local_entropy, 4),
                    "surprisal_kl": round(fp.surprisal_kl, 4),
                    "score": round(fp.score, 4),
                    "top_tokens": fp.top_tokens,
                }
                for fp in self.top_k
            ],
        }


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    entries: Optional[List[dict]] = None,
    *,
    window_size: int = 40,
    step: int = 10,
    k: int = 5,
    alpha: float = 0.5,
    agent: str = "albedo",
) -> FocusNarrowerResult:
    """
    Identify the K most attention-worthy windows in the qualia stream.

    Args:
        entries     : list of qualia/memory entry dicts with 'content' or 'text'.
        window_size : tokens per sliding window.
        step        : stride between windows.
        k           : number of focus points to return.
        alpha       : weight for local entropy vs. KL surprisal (0–1).
    """
    if entries is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
        except Exception:
            entries = []

    stream = _to_token_stream(entries)
    if not stream:
        return FocusNarrowerResult()

    bg_counts = Counter(stream)
    bg_entropy = _entropy(bg_counts)

    # Slide window
    scored = []
    i = 0
    while i + window_size <= len(stream):
        window = stream[i: i + window_size]
        local_c = Counter(window)
        h = _entropy(local_c)
        kl = _kl_div(local_c, bg_counts)
        score = alpha * h + (1 - alpha) * kl
        top = [tok for tok, _ in local_c.most_common(5)]
        scored.append((score, h, kl, i, i + window_size, window, top))
        i += step

    if not scored:
        return FocusNarrowerResult()

    all_scores = [s[0] for s in scored]
    mean_score = sum(all_scores) / len(all_scores)

    # Greedy NMS
    scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
    selected: List[FocusPoint] = []
    selected_centres: List[float] = []

    for sc, h, kl, start, end, window, top in scored_sorted:
        centre = (start + end) / 2.0
        if any(abs(centre - c) < window_size for c in selected_centres):
            continue
        rank = len(selected) + 1
        selected.append(FocusPoint(
            rank=rank,
            start_idx=start,
            end_idx=end,
            window_tokens=window,
            local_entropy=h,
            surprisal_kl=kl,
            score=sc,
            top_tokens=top,
        ))
        selected_centres.append(centre)
        if len(selected) >= k:
            break

    focus_ratio = (
        (sum(fp.score for fp in selected) / len(selected)) / (bg_entropy or 1.0)
        if selected else 0.0
    )

    return FocusNarrowerResult(
        top_k=selected,
        background_entropy=bg_entropy,
        mean_score=mean_score,
        focus_ratio=focus_ratio,
    )
