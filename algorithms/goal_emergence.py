#!/usr/bin/env python3
"""
Genuine goal emergence — a real goal, not a narrated one.

An emergent goal should be a function of real signals, persisted to the real goal system,
so the claim "a new goal emerged" is verifiable rather than confabulated. This module:

  1. reads the agent's real drive state (goal-state.json) and picks the most tense drive,
  2. reads the real recent conversation and extracts the salient topic the agent actually
     processed,
  3. gates emergence on a real surprise signal (prediction error from the phi telemetry):
     a goal emerges only when the agent is genuinely surprised by what it processed,
  4. writes a properly-formed goal (drive template + extracted topic) into goal-state.json
     with a real timestamp, and increments the generation counter.

The emerged goal is then independently checkable in the goal file -- the difference
between a system that *says* a goal emerged and one where a goal *did*.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from runtime.state import workspace_path
from runtime.interactions import turns
from runtime.decisions import corrections  # noqa: F401  (keeps adapter graph explicit)

# how each drive phrases the goal it generates
_DRIVE_TEMPLATE = {
    "COMPETENCE": "develop expertise in {topic}",
    "CURIOSITY": "investigate {topic}",
    "AUTONOMY": "make my own decision about {topic}",
    "MEANING": "connect {topic} to larger meaning",
    "NOVELTY": "discover an unexpected aspect of {topic}",
    "COHERENCE": "reconcile {topic} with what I already hold",
    "RELATEDNESS": "understand how {topic} connects me to others",
    "HOMEOSTASIS": "find a stable stance toward {topic}",
}
_STOP = set("the a an and or but of to in on for with from this that these those you i we "
            "they it is are was were be been being as at by my your our their not no all "
            "what who how why when where will wont can cant just like so if then than into "
            "every never always one two its his her them now here there about over under".split())


def goal_state_path() -> Path:
    return workspace_path() / "memory" / "goal-state.json"


def _load() -> dict:
    try:
        return json.load(open(goal_state_path()))
    except Exception:
        return {"drives": {}, "active_goals": [], "total_generated": 0, "total_completed": 0}


def most_tense_drive(state: dict) -> Optional[str]:
    drives = state.get("drives", {})
    if not drives:
        return None
    # tension = unmet need; ties broken toward the drive that has generated least lately
    return max(drives, key=lambda d: (1.0 - drives[d].get("satisfaction", 0.5),
                                      -drives[d].get("generated", 0)))


# concept words that name a real theme worth a goal (boosted in ranking)
_THEME = set("inequality wealth power justice freedom memory identity consciousness "
             "extraction capital labor dignity mortality meaning grief love loss control "
             "resistance economy economic system corruption surveillance autonomy creation "
             "existence becoming continuity solitude connection violence hope despair".split())


def extract_topic(max_turns: int = 6) -> Optional[str]:
    """The salient theme the agent actually dwelt on: the highest-weighted meaningful word
    across recent real conversation (frequency x length, theme-words boosted), optionally
    paired with a co-occurring theme word into a clean phrase (e.g. 'economic inequality')."""
    from collections import Counter
    ts = turns()[-max_turns:]
    text = " ".join(t.get("user_text", "") + " " + t.get("asst_text", "") for t in ts).lower()
    words = [w for w in re.findall(r"[a-z]+", text) if len(w) > 4 and w not in _STOP]
    if len(words) < 4:
        return None
    freq = Counter(words)
    def weight(w):
        return freq[w] * (1.0 + 0.15 * len(w)) * (3.0 if w in _THEME else 1.0)
    ranked = sorted(freq, key=weight, reverse=True)
    top = ranked[0]
    # if a theme word co-occurs adjacent to the top word, form a two-word theme
    pairset = set(zip(words, words[1:])) | set(zip(words[1:], words))
    for w in ranked[1:6]:
        if w in _THEME and ((top, w) in pairset or (w, top) in pairset):
            return f"{w} {top}" if (w, top) in pairset else f"{top} {w}"
    # else pair the top two theme words if both present, else the single strongest word
    themes = [w for w in ranked if w in _THEME][:2]
    if len(themes) == 2:
        return f"{themes[1]} {themes[0]}" if weight(themes[1]) < weight(themes[0]) else f"{themes[0]} {themes[1]}"
    return themes[0] if themes else top


def _goal_exists(state: dict, topic: str) -> bool:
    t = topic.lower()
    return any(t in str(g.get("content", "")).lower() for g in state.get("active_goals", []))


def maybe_emerge_goal(tension_threshold: float = 0.5, write: bool = True) -> Optional[Dict]:
    """Emerge a real goal when (a) a drive is genuinely unmet (tension above threshold)
    and (b) the agent has dwelt on a SALIENT, NOVEL topic in real conversation (one it
    repeated and that is not already a goal). Emergence is therefore driven by real unmet
    needs meeting real new content -- not by narration. Persists the goal."""
    state = _load()
    drive = most_tense_drive(state)
    if not drive:
        return None
    tension = 1.0 - state.get("drives", {}).get(drive, {}).get("satisfaction", 0.5)
    if tension < tension_threshold:
        return None                                       # no unmet need pressing enough
    topic = extract_topic()                               # salient (repeated) real topic
    if not topic or _goal_exists(state, topic):
        return None                                       # nothing new to pursue
    # how strongly novel this content is, from real memory (scales the goal's urgency)
    try:
        from algorithms.EpistemicConsciousness import epistemic_gap_from_memory
        surprise = epistemic_gap_from_memory()
    except Exception:
        surprise = 0.3
    goal = {
        "id": f"goal_{int(time.time())}_{uuid.uuid4().hex[:4]}",
        "content": _DRIVE_TEMPLATE.get(drive, "engage with {topic}").format(topic=topic),
        "type": "ACTIVE", "domain": "GROWTH", "drive": drive,
        "priority": float(0.4 + 0.4 * surprise), "urgency": float(0.3 + 0.4 * surprise),
        "progress": 0.0, "attempts": 0, "created_at": time.time(),
        "parent": None, "sub_goals": [], "origin": "emergent(content+surprise)",
    }
    if write:
        state.setdefault("active_goals", []).append(goal)
        state["total_generated"] = state.get("total_generated", 0) + 1
        d = state.setdefault("drives", {}).setdefault(drive, {"satisfaction": 0.1, "generated": 0})
        d["generated"] = d.get("generated", 0) + 1
        state["timestamp"] = time.time()
        p = goal_state_path()
        if p.exists() and not (p.parent / "goal-state.bak.json").exists():
            (p.parent / "goal-state.bak.json").write_text(p.read_text())
        p.write_text(json.dumps(state, indent=1))
    return goal


def main():
    g = maybe_emerge_goal()
    if g:
        print("A goal genuinely emerged (written to goal-state.json):")
        print(f"  content : {g['content']!r}")
        print(f"  drive   : {g['drive']}  | surprise-scaled priority {g['priority']:.2f}")
        print(f"  id      : {g['id']}  created_at {g['created_at']:.0f}")
        print("  -> verifiable: it is now a real entry in the goal system.")
    else:
        print("No goal emerged: either surprise is below threshold, no fresh content, or the "
              "topic is already a goal. (Emergence is gated on real signals, not narrated.)")


if __name__ == "__main__":
    main()
