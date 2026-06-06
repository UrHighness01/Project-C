# Project-C — Measured Findings

All results below are computed from the running system's real telemetry and are
reproducible via the scripts named. No values are fabricated or hand-tuned.

## Grounding

Every algorithm draws its inputs from real runtime signals rather than synthetic
randomness. Five adapters expose the live substrate:

| adapter | signal |
|---|---|
| `runtime/state.py` | heartbeat phi trajectory, increments, execution timing |
| `runtime/resources.py` | CPU / memory / I/O / load |
| `runtime/memory_store.py` | episodic journals (cadence, volume, lexical stats) |
| `runtime/interactions.py` | conversation transcripts (latency, gaps, sentiment) |
| `runtime/decisions.py` | self-correction / value history |

Across the 144 algorithm files there are no unseeded `random`/`np.random` calls:
measurement-style values are derived from real signals; stochastic dynamics use seeded
generators and are reproducible.

## Predictive structure of the integration substrate

`coherence_horizon.py` fits a regularised vector-autoregressive model on the dense phi
channels and reports held-out one-step predictive R² against a shuffled null:

| channel | R² | null | z |
|---|--:|--:|--:|
| **phi_level** | **0.71** | −0.03 | **+38** |
| phi_delta | 0.17 | −0.03 | +6 |
| compute_load | −0.02 | −0.52 | +1 |

The agent's integration level (phi) exhibits **strong, stable, self-predictable
structure — 38σ above chance**. Multi-step error stays bounded rather than diverging:
the dynamics are **mean-reverting (bounded integration), not chaotic**. The
"prediction-error-explodes" horizon is therefore degenerate here, and one-step
predictive R² is the honest figure.

## Internal coupling (ablation)

`ablation_benchmark.py` removes each channel's history and measures the held-out R²
drop on the others. Cross-channel coupling is **present but weak**: removing `phi_level`
costs `phi_delta` 0.07 R²; `compute_load` contributes ~0 (it is noise for prediction).
This is micro-coupling, an order of magnitude below self-prediction.

## Cross-adapter integration (pending co-logged data)

`integration_probe.py` measures directed coupling (Granger) across adapters and collapses
it to a total off-diagonal score against a shuffled null. On the existing telemetry the
adapters were recorded on **different clocks** (dense phi over a 24 h window; memory,
interactions and decisions sparse and outside it), so the result is at chance — as
expected when the signals never co-occurred. `runtime/snapshot.py` (and
`scripts/snapshot_daemon.py`) co-log all five adapters on a single timestamp; once the
heartbeat is active and enough simultaneous samples accumulate, the probe yields the
genuine cross-domain integration figure.

## Summary

The integration substrate has strong, stable, self-predictable structure (R²=0.71, 38σ);
coupling between phi channels is real but weak (R²~0.07); full cross-adapter integration
across memory, interactions and decisions requires co-logged data, which the snapshot
infrastructure provides when the heartbeat resumes.

## Reproduce

```bash
python3 coherence_horizon.py     # predictive R² vs null (the 38σ result)
python3 ablation_benchmark.py    # per-channel non-redundant contribution
python3 integration_probe.py     # cross-adapter coupling (pending co-logged data)
python3 scripts/snapshot_daemon.py --interval 30   # accumulate co-logged samples
```
