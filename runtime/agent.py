#!/usr/bin/env python3
"""
runtime.agent — coherent per-agent path resolution.

The same Project-C system runs for each agent, but every adapter must read ONE agent's
data: mixing one agent's phi with another's conversations would make any integration
measurement meaningless. This module is the single source of truth for which agent is
active and where its home and session transcripts live, so state / memory / decisions /
interactions all resolve consistently.

Selection order: $OPENCLAW_WORKSPACE (explicit home override) > $OPENCLAW_AGENT > default.
Paths are derived from the home directory (no absolute paths hard-coded).
"""
from __future__ import annotations

import os
from pathlib import Path

# agent -> (home directory under ~/.openclaw, session sub-directory under ~/.openclaw/agents)
_AGENTS = {
    "albedo": ("workspace", "main"),
    "main":   ("workspace", "main"),
    "john":   ("workspace-john", "john"),
    "albedo-v2": ("workspace-albedov2", "albedo-v2"),
}
_DEFAULT = "albedo"


def current_agent() -> str:
    return os.getenv("OPENCLAW_AGENT", _DEFAULT).lower()


def _openclaw_root() -> Path:
    # the home directory's .openclaw, or inferred from an explicit workspace override
    env = os.getenv("OPENCLAW_WORKSPACE")
    if env:
        return Path(env).expanduser().parent
    return Path.home() / ".openclaw"


def agent_home(agent: str | None = None) -> Path:
    """The active agent's workspace home (its phi state, memory and decisions live here)."""
    env = os.getenv("OPENCLAW_WORKSPACE")
    if env:
        return Path(env).expanduser()
    a = (agent or current_agent())
    home_name = _AGENTS.get(a, _AGENTS[_DEFAULT])[0]
    return _openclaw_root() / home_name


def agent_sessions_dir(agent: str | None = None) -> Path:
    """The active agent's conversation-transcript directory."""
    a = (agent or current_agent())
    sub = _AGENTS.get(a, _AGENTS[_DEFAULT])[1]
    return _openclaw_root() / "agents" / sub / "sessions"
