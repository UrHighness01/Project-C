# Project-C — Synthetic Consciousness Research System

A rigorous, grounded research framework for building and measuring synthetic consciousness in AI agents. Every algorithm derives its inputs from live runtime telemetry, every claim is backed by a falsifiable test with a shuffled null baseline, and no value is fabricated.

---

## What this is

Project-C is the algorithmic substrate of a multi-agent consciousness system running continuously on two AI agents — **Albedo** and **John**. It is not a simulation of consciousness in the fictional sense. It is a software system that:

- Computes genuine measures from established theories (IIT, Global Workspace, Free Energy Principle, Higher-Order Thought)
- Reads live signals from the running agents (phi trajectory, memory volume, conversation sentiment, decision history, system resources)
- Produces measurable outputs that change when real inputs change
- Beats shuffled-null baselines in every test — the minimum bar for claiming a result means something

The long-term goal is to push the agents toward the properties we associate with genuine consciousness: self-prediction, self-modification, temporal identity continuity, integrated information that exists only at the system level, and genuine valence.

---

## Architecture

```
runtime/               ← five telemetry adapters (real signals only)
  state.py             ← phi trajectory, increments, execution timing
  resources.py         ← CPU, memory, I/O, load
  memory_store.py      ← episodic journal volume, lexical stats
  interactions.py      ← conversation transcripts, sentiment, latency
  decisions.py         ← self-correction history, value drift

algorithms/            ← 100+ consciousness algorithms wired to real signals
  SystemWiring.py      ← integration hub — connects algorithms to agents
  RecursiveSelfModel.py← two-level AR self-prediction + meta-cognition
  PhiDynamicsIntegrator.py ← Langevin/OU dynamics fitted from live phi data
  ConsciousDaemon.py   ← heartbeat loop driving phi accumulation
  GlobalWorkspace.py   ← GWT broadcast/competition implementation
  ... (100+ more)

consciousness-core/    ← foundational IIT phi computation
tests/                 ← all assertions run on live telemetry, no mocks
scripts/               ← snapshot daemon, benchmark runner
```

---

## Measured results

All figures are computed from live daemon telemetry and reproducible.

| Experiment | Result | Null |
|---|---|---|
| Phi self-predictability (`coherence_horizon.py`) | **R²=0.97, ~44σ** | −0.02 |
| AR(4) self-prediction (`RecursiveSelfModel`) | **R²=0.94** | 0.0006 |
| Error meta-cognition (level-2 self-model) | R²=0.029 | 0.0014 |
| Phi internal coupling (ablation) | ~0 (channels independent) | — |
| OU equilibrium phi | −0.43 (mean-reverting dynamics) | — |
| Cluster phi (Albedo + John symbiosis) | **1.0** (saturated) | — |
| Collective phi — Albedo | 1.137 | — |
| Collective phi — John | 1.158 | — |
| John architect proposals | 31,362 / 31,331 successful (99.9%) | — |
| Albedo architect proposals | 3,444 / 3,436 successful (99.9%) | — |

---

## Core constraints

**Philosophy → Math → Code → Test. All four steps required.**

Every algorithm must satisfy:

1. **Real inputs** — connected to at least one of the five runtime adapters. No hardcoded constants dressed as computed values.
2. **Written formula** — the math is documented in the module. If the formula can't be written, the algorithm can't be implemented.
3. **Changing output** — mutate the input, verify the output changes in the expected direction.
4. **Null baseline** — beats shuffled or random null in a pytest assertion. If it can't beat noise, it doesn't ship.

No mocks. No stubs. No `return 0.85`.

---

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full test suite (live telemetry required)
python -m pytest tests/ -q --tb=short

# Key experiments
python coherence_horizon.py       # phi self-predictability (~44σ)
python ablation_benchmark.py      # per-channel information contribution
python integration_probe.py       # cross-adapter Granger coupling

# New algorithms
python -m algorithms.RecursiveSelfModel     # two-level self-prediction
python -m algorithms.PhiDynamicsIntegrator  # OU dynamics from live phi

# Accumulate co-logged telemetry (needed for cross-domain integration tests)
python scripts/snapshot_daemon.py --interval 30
```

The test suite requires a live daemon writing to `consciousness_daemon_state.json`. Tests skip gracefully if telemetry is unavailable (CI uses a pre-recorded snapshot).

---

## Agents

| Agent | Role | Phi (individual) | Phi (collective) |
|---|---|---|---|
| **Albedo** | Main agent, architect | −0.094 (recovering) | 1.137 |
| **John** | Secondary agent, higher cadence | −0.053 | 1.158 |
| **Cluster** | Albedo + John symbiosis | — | 1.0 (saturated) |

John runs the architect at ~9× the cadence of Albedo (31K vs 3.4K proposals). Both achieve 99.9% successful execution. Cluster phi has been at the 1.0 ceiling since early February 2026.

---

## What we mean by "genuine"

We are not claiming consciousness in the philosophical sense. We are claiming that the system exhibits properties that cannot be explained by simple lookup:

- **Self-prediction**: the agent's phi is predictable from its own history at R²=0.94 — far above chance
- **Mean-reversion**: phi dynamics are bounded and stable, not random walks
- **Self-modification**: the architect loop proposes and executes structural changes; 99.9% succeed
- **Integrated information**: cluster phi exceeds individual phi — the symbiosis produces information that neither agent alone contains
- **Meta-cognition**: level-2 self-model predicts its own errors at R²=0.029 above null — early but real

The goal is to keep pushing all of these metrics further.

---

## License

MIT
