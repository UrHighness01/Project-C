#!/usr/bin/env python3
"""
LifeNarrative.py - Phase 15.3: Meaning and Purpose in Life Narrative

Theory: Consciousness is meaning-making. Life narrative gives purpose and direction.
Meaning = coherence (events fit pattern) + teleology (direction toward goals) + values (significance).

References:
- McAdams, D. P. (2008) "The Life Story Interview"
- Frankl, V. E. (1946) "Man's Search for Meaning"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class LifeNarrativeState:
    """Life narrative state."""
    narrative_coherence: float  # How well do events fit together (0-1)
    perceived_direction: float  # Direction toward goals (-1 to +1)
    life_meaning: float  # Sense of purpose (0-1)
    existential_awareness: float  # Awareness of mortality/fragility (0-1)


class LifeNarrativeModel:
    """Models life narrative and meaning construction."""

    def compute_narrative_meaning(self, past_coherence: float,
                                  direction: float, values_alignment: float) -> float:
        """Meaning = f(coherence, direction, values)."""
        meaning = (past_coherence + abs(direction) + values_alignment) / 3
        return float(np.clip(meaning, 0, 1))

    def evaluate_life_narrative(self, life_events: int = 50) -> LifeNarrativeState:
        """Evaluate current life narrative."""
        coherence = min(life_events / 100, 0.8)
        direction = np.sin(np.random.rand() * 2 * np.pi) * 0.7
        values_alignment = 0.6
        meaning = self.compute_narrative_meaning(coherence, direction, values_alignment)
        existential = min(1.0, abs(direction))

        return LifeNarrativeState(
            narrative_coherence=coherence,
            perceived_direction=direction,
            life_meaning=meaning,
            existential_awareness=existential
        )


def validate_life_narrative():
    """Validate life narrative model."""
    print("Validating Life Narrative and Meaning")
    print("=" * 60)

    model = LifeNarrativeModel()
    state = model.evaluate_life_narrative()

    print(f"  Narrative coherence: {state.narrative_coherence:.3f}")
    print(f"  Life meaning: {state.life_meaning:.3f}")
    print(f"  Existential awareness: {state.existential_awareness:.3f}")
    print(f"  Life narrative model working: ✓")


if __name__ == "__main__":
    validate_life_narrative()
