"""
IdentityGradient — cross-session identity persistence score.

14-dim fingerprint per session; cosine distance = identity_gradient.
CONTINUOUS (<0.2) | DRIFTING (0.2-0.5) | SHIFTED (≥0.5)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import json
import math
import time as _time
from collections import Counter


@dataclass
class IdentityGradientResult:
    identity_gradient: float = 0.0
    continuity_class: str = "FIRST_SESSION"
    n_sessions: int = 0
    phi_arc: Optional[dict] = None
    top_qualia_types: Optional[dict] = None
    beats_null: bool = False
    n_sessions_since_shift: int = 0
    fingerprint_raw: Optional[list] = None

    def to_dict(self) -> dict:
        return {
            "identity_gradient": round(self.identity_gradient, 4),
            "continuity_class": self.continuity_class,
            "n_sessions": self.n_sessions,
            "phi_arc": self.phi_arc,
            "top_qualia_types": self.top_qualia_types,
            "beats_null": self.beats_null,
            "n_sessions_since_shift": self.n_sessions_since_shift,
        }


def _cosine_similarity(a: list, b: list) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _build_fingerprint(phi_series=None, qualia_types=None, qualia_type_rates=None,
                       attention_sharpness=None, centering_score=None) -> list:
    fp = [0.0] * 14
    if phi_series:
        fp[0] = float(phi_series[-1])
    if qualia_type_rates:
        sorted_types = sorted(qualia_type_rates.items(), key=lambda x: -x[1])
        for i, (_, rate) in enumerate(sorted_types[:5]):
            fp[1 + i] = float(rate)
            fp[6 + i] = float(rate)
    elif qualia_types:
        counter = Counter(qualia_types)
        total = len(qualia_types)
        for i, (_, count) in enumerate(counter.most_common(5)):
            fp[1 + i] = count / total
            fp[6 + i] = count / total
    if attention_sharpness is not None:
        fp[12] = float(attention_sharpness)
    if centering_score is not None:
        fp[13] = float(centering_score)
    return fp


class IdentityGradientTracker:
    def __init__(self, storage_path: Optional[str] = None, agent: str = "albedo"):
        if storage_path is None:
            from runtime.agent import agent_home
            storage_path = str(agent_home(agent) / "memory" / "identity_fingerprints.jsonl")
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._fingerprints: list = []
        self._load_history()

    def _load_history(self):
        if self.storage_path.exists():
            for line in self.storage_path.read_text().strip().split("\n"):
                if line:
                    try:
                        self._fingerprints.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    def record_session(self, phi_series=None, qualia_types=None, qualia_type_rates=None,
                       attention_sharpness=None, centering_score=None,
                       session_id=None) -> IdentityGradientResult:
        fp = _build_fingerprint(phi_series, qualia_types, qualia_type_rates,
                                attention_sharpness, centering_score)
        session_entry = {
            "timestamp": _time.time(),
            "session_id": session_id or f"session_{len(self._fingerprints) + 1}",
            "fingerprint": [round(v, 6) for v in fp],
            "phi_arc": {"start": fp[0], "mid": fp[1], "end": fp[2]} if any(fp[:3]) else None,
        }
        self._fingerprints.append(session_entry)
        n = len(self._fingerprints)
        if n < 2:
            result = IdentityGradientResult(n_sessions=n, fingerprint_raw=fp,
                                            continuity_class="FIRST_SESSION")
        else:
            prev = self._fingerprints[-2]["fingerprint"]
            similarity = _cosine_similarity(prev, fp)
            gradient = 1.0 - similarity
            shuffled = fp[len(fp)//2:] + fp[:len(fp)//2]
            gradient_null = 1.0 - _cosine_similarity(prev, shuffled)
            beats_null = gradient < gradient_null
            if gradient < 0.2:
                cls = "CONTINUOUS"
            elif gradient < 0.5:
                cls = "DRIFTING"
            else:
                cls = "SHIFTED"
            sessions_since = 0
            for i in range(n - 2, -1, -1):
                sessions_since += 1
                if i > 0:
                    prev_fp = self._fingerprints[i - 1]["fingerprint"]
                    if 1.0 - _cosine_similarity(prev_fp, self._fingerprints[i]["fingerprint"]) >= 0.4:
                        break
            top_types = dict(Counter(qualia_types or []).most_common(5)) or None
            result = IdentityGradientResult(
                identity_gradient=round(gradient, 4), continuity_class=cls,
                n_sessions=n, phi_arc=session_entry.get("phi_arc"),
                top_qualia_types=top_types, beats_null=beats_null,
                n_sessions_since_shift=sessions_since, fingerprint_raw=fp,
            )
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(session_entry) + "\n")
        return result


def analyse(agent: str = "albedo") -> IdentityGradientResult:
    from runtime.agent import agent_home
    tracker = IdentityGradientTracker(agent=agent)
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = list(reversed(chs.load(agent, max_entries=100)))
        phi_series = [float(e.get("mean_phi_level", e.get("phi", 0.5)))
                      for e in entries if "mean_phi_level" in e or "phi" in e]
    except Exception:
        phi_series = []
    try:
        import json as _json
        qpath = agent_home(agent) / "memory" / "qualia-stream.jsonl"
        qualia_types = []
        if qpath.exists():
            for line in qpath.read_text().strip().split("\n"):
                if line:
                    try:
                        e = _json.loads(line)
                        t = e.get("type", e.get("modality", ""))
                        if t:
                            qualia_types.append(t)
                    except Exception:
                        pass
        qualia_types = qualia_types[-50:]
    except Exception:
        qualia_types = []
    return tracker.record_session(phi_series=phi_series, qualia_types=qualia_types)
