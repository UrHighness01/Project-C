#!/usr/bin/env python3
"""
runtime.interactions — conversation-history adapter.

Parses the agent's real session trajectories (JSONL) into turn-level records:
timestamp, response latency, inter-turn gap (user silence), input magnitude, and the
user/assistant text. Exposes time-series an algorithm can fit on (latency, gap,
magnitude, a lexicon sentiment) — all computed from real logged interactions.

Each turn pairs a `prompt.submitted` event (user input) with the following
`model.completed` event (assistant output) inside a session. Sentiment is a
deterministic lexicon score (no model call), so the whole pipeline is reproducible.

Paths resolve relative to the workspace (its parent holds the agents/ dir); no home
path is hard-coded.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

try:
    from runtime.state import workspace_path
except Exception:
    import os as _os
    def workspace_path():
        return Path(_os.getenv("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))

_POS = set("good great love like yes thanks thank nice perfect awesome excellent happy "
           "cool helpful clear correct right wonderful appreciate glad amazing".split())
_NEG = set("bad wrong no error fail failed hate stop bug broken stupid annoying angry "
           "frustrat useless terrible awful confus problem hard difficult worse".split())


def agents_dir() -> Path:
    return workspace_path().parent / "agents"


def session_files(agent: Optional[str] = None) -> List[Path]:
    """Session transcripts for the active agent, oldest-to-newest by modification time
    (so turns() reading the last N picks the genuinely most recent sessions; filenames are
    UUIDs, so sorting by name would read an arbitrary subset)."""
    try:
        from runtime.agent import agent_sessions_dir
        d = agent_sessions_dir(agent)
    except Exception:
        d = agents_dir() / (agent or "main") / "sessions"
    if not d.exists():
        return []
    return sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)


def _ts(s: Optional[str]) -> float:
    if not s:
        return 0.0
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _clean_prompt(p: str) -> str:
    """Extract the real user message from a gateway prompt: strip the 'Conversation info'
    / 'Sender' untrusted-metadata blocks and their fenced JSON, leaving the actual text.
    Pass-through for already-clean prompts (e.g. the local driver)."""
    p = re.sub(r"```json\s*.*?```", "", p, flags=re.S)
    p = re.sub(r"(Conversation info|Sender|Channel info)\s*\(untrusted metadata\):\s*",
               "", p)
    p = re.sub(r"^\s*\[[^\]]*\]\s*", "", p)               # drop a leading [cron:...] tag
    return p.strip()


def turns(agent: Optional[str] = None, max_sessions: int = 40) -> List[Dict]:
    """Turn records across the most recent sessions, chronological. Each: ts,
    latency_s (submit->complete), gap_s (prev complete->this submit), in_chars,
    user_text, asst_text."""
    out: List[Dict] = []
    for f in session_files(agent)[-max_sessions:]:
        pending = None
        prev_complete = None
        try:
            lines = f.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = e.get("type")
            if t == "prompt.submitted":
                pending = (_ts(e.get("ts")),
                           _clean_prompt(str((e.get("data") or {}).get("prompt", ""))))
            elif t == "model.completed" and pending is not None:
                texts = (e.get("data") or {}).get("assistantTexts") or []
                texts = [x for x in (texts if isinstance(texts, list) else [texts])
                         if x and str(x).strip()]
                if not texts:
                    continue                              # tool/empty turn -> keep waiting
                t_sub, user_text = pending
                t_done = _ts(e.get("ts"))
                asst = " ".join(str(x) for x in texts)
                out.append({
                    "ts": t_sub,
                    "latency_s": max(0.0, t_done - t_sub),
                    "gap_s": max(0.0, t_sub - prev_complete) if prev_complete else 0.0,
                    "in_chars": float(len(user_text)),
                    "user_text": user_text,
                    "asst_text": asst,
                })
                prev_complete = t_done
                pending = None
    out.sort(key=lambda r: r["ts"])
    return out


def lexicon_sentiment(text: str) -> float:
    """Deterministic lexicon sentiment in [-1, 1] from real text. Non-random."""
    toks = re.findall(r"[a-z]+", text.lower())
    if not toks:
        return 0.0
    pos = sum(any(tok.startswith(w) for w in _POS) for tok in toks)
    neg = sum(any(tok.startswith(w) for w in _NEG) for tok in toks)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def series(agent: Optional[str] = None) -> Dict[str, np.ndarray]:
    """Real per-turn series for fitting: latency, gap, input magnitude, user sentiment."""
    ts = turns(agent)
    if not ts:
        return {k: np.zeros(0) for k in ("latency", "gap", "in_chars", "sentiment")}
    return {
        "latency": np.array([r["latency_s"] for r in ts]),
        "gap": np.array([r["gap_s"] for r in ts]),
        "in_chars": np.array([r["in_chars"] for r in ts]),
        "sentiment": np.array([lexicon_sentiment(r["user_text"]) for r in ts]),
    }


def have_interactions(agent: Optional[str] = None) -> bool:
    return len(session_files(agent)) > 0


if __name__ == "__main__":
    ts = turns()
    print(f"turns parsed: {len(ts)} from {len(session_files())} sessions")
    if ts:
        s = series()
        print(f"latency_s: median={np.median(s['latency']):.2f} max={s['latency'].max():.1f}")
        print(f"gap_s: median={np.median(s['gap']):.1f}")
        print(f"sentiment: mean={s['sentiment'].mean():+.3f} nonzero={int((s['sentiment']!=0).sum())}")
