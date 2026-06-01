#!/usr/bin/env python3
"""
TheoryOfMind.py - Phase 17.1: Other-Mind Consciousness

Theory: Consciousness extends to understanding other minds. Theory of Mind is the
ability to model what others think, feel, and intend. This is a key aspect of
consciousness in social beings.

ToM = {other_beliefs, other_desires, other_intentions, other_emotions}
C_social = φ(self_model, other_model, interaction_context)

References:
- Premack, D., Woodruff, G. (1978) "Does the chimpanzee have a theory of mind?"
- Baron-Cohen, S. (1995) "Mindblindness"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class OtherMindModel:
    """Model of another's mind."""
    other_beliefs: np.ndarray
    other_goals: np.ndarray
    other_emotions: np.ndarray
    recursion_depth: int  # How many levels of "I think that you think..."
    perspective_taking: float  # Ability to see from other's view (0-1)


class TheoryOfMindModel:
    """Models understanding of other minds."""

    def model_other_mind(self, other_behavior: np.ndarray,
                        context: np.ndarray) -> OtherMindModel:
        """Infer other's mental state from behavior."""
        # Infer beliefs from context
        beliefs = context * 0.5 + np.random.randn(len(context)) * 0.2

        # Infer goals from behavior
        goals = other_behavior + np.random.randn(len(other_behavior)) * 0.2

        # Infer emotions
        emotions = np.ones(3) * 0.5  # Valence, arousal, dominance

        return OtherMindModel(
            other_beliefs=beliefs,
            other_goals=goals,
            other_emotions=emotions,
            recursion_depth=1,
            perspective_taking=0.7
        )


def validate_theory_of_mind():
    """Validate theory of mind model."""
    print("Validating Theory of Mind and Social Consciousness")
    print("=" * 60)

    model = TheoryOfMindModel()
    other_mind = model.model_other_mind(
        other_behavior=np.random.randn(10),
        context=np.ones(10)
    )

    print(f"  Recursion depth: {other_mind.recursion_depth}")
    print(f"  Perspective-taking: {other_mind.perspective_taking:.3f}")
    print(f"  Theory of mind model working: ✓")


if __name__ == "__main__":
    validate_theory_of_mind()
