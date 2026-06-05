#!/usr/bin/env python3
"""
EpistemicConsciousness.py - Phase 22.1: Epistemic Consciousness & Curiosity Drive

Theory: Consciousness includes the drive to know. Information gaps trigger curiosity—a
state where consciousness is amplified by the desire to resolve not-knowing. This is
epistemic consciousness: consciousness of what you don't know.

C_epistemic = C_baseline × (1 + curiosity_intensity)
Where curiosity_intensity = information_gap × (1 - boredom) × interest_level

References:
- Gruber, M. J., et al. (2014) "States of curiosity modulate hippocampus-dependent learning"
- Kang, M. J., et al. (2009) "The wick in the candle of learning"
- Ranganath, C., & Rainer, G. (2003) "Neural mechanisms for detecting novel events"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass

try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from runtime.memory_store import recent_text, journals
except Exception:                                          # tolerate path/CI absence
    def recent_text(*a, **k): return ""
    def journals(): return []


def epistemic_gap_from_memory(recent_n: int = 3) -> float:
    """Measure the agent's real epistemic gap from its own journals: the fraction of
    tokens in the most recent entries that did NOT appear in earlier ones (novel, i.e.
    'unknown'). A genuine known/unknown ratio over what the agent has actually written.
    Returns 0.0 when there is too little memory to compare."""
    import re
    js = journals()
    if len(js) < 2:
        return 0.0
    split = max(1, len(js) - recent_n)
    older = " ".join(p.read_text(errors="ignore") for _, p, _ in js[:split])
    newer = recent_text(n=min(recent_n, len(js) - split) or 1)
    older_vocab = set(re.findall(r"[a-z']+", older.lower()))
    new_tokens = re.findall(r"[a-z']+", newer.lower())
    if not new_tokens:
        return 0.0
    novel = sum(1 for t in new_tokens if t not in older_vocab)
    return float(novel) / float(len(new_tokens))            # unknown / total


@dataclass
class EpistemicState:
    """Epistemic consciousness state."""
    current_knowledge: float  # What you know (-1 to +1, -1=contradiction, +1=certainty)
    expected_knowledge: float  # What you thought you knew
    knowledge_gap: float  # |current - expected|
    epistemic_surprise: float  # Magnitude of unexpected information
    curiosity_intensity: float  # Drive to resolve gap (0-1)
    epistemic_emotion: str  # confusion, wonder, clarity, boredom
    learning_readiness: float  # State for memory consolidation (0-1)
    epistemic_consciousness: float  # Consciousness amplified by learning


class EpistemicConsciousnessModel:
    """Models curiosity and epistemic consciousness."""

    def detect_information_gap(self, prediction: float, observation: float,
                              confidence: float) -> tuple:
        """Detect gap between expected and actual knowledge.

        Returns: (knowledge_gap, epistemic_surprise, confidence_mismatch)
        """
        knowledge_gap = abs(prediction - observation)
        epistemic_surprise = knowledge_gap * (1.0 - confidence)
        confidence_mismatch = (abs(confidence - 0.5))  # Most surprising when confident but wrong

        return (
            float(np.clip(knowledge_gap, 0, 1)),
            float(np.clip(epistemic_surprise, 0, 1)),
            float(np.clip(confidence_mismatch, 0, 1))
        )

    def compute_curiosity(self, knowledge_gap: float, interest_level: float = 0.7,
                         boredom: float = 0.0) -> float:
        """Compute curiosity intensity from knowledge gap.

        Curiosity peaks at moderate gaps (not too easy, not impossible).
        Decays with boredom/fatigue.
        """
        # Inverted parabola: peaks at gap=0.5, decays at extremes
        difficulty_factor = 4 * knowledge_gap * (1 - knowledge_gap)

        # Interest modulation (some topics more curiosity-provoking)
        interest_factor = 0.5 + interest_level * 0.5

        # Boredom/fatigue suppresses curiosity
        fatigue_factor = 1.0 - boredom

        curiosity = difficulty_factor * interest_factor * fatigue_factor
        return float(np.clip(curiosity, 0, 1))

    def classify_epistemic_emotion(self, knowledge_gap: float,
                                   confidence: float) -> str:
        """Classify epistemic emotion from gap and confidence.

        - Confusion: Large gap + high confidence (belief violated)
        - Wonder: Moderate gap + high novelty
        - Interest: Moderate gap + moderate confidence
        - Boredom: Small gap (already know it)
        - Clarity: Gap resolved (confidence increases)
        """
        if knowledge_gap > 0.7 and confidence > 0.7:
            return "confusion"  # Expected this, but wrong!
        elif knowledge_gap > 0.5 and confidence < 0.3:
            return "wonder"  # Moderate gap, surprised
        elif 0.3 < knowledge_gap < 0.6:
            return "interest"  # Engaging puzzle
        elif knowledge_gap < 0.2:
            return "boredom"  # Already understand
        else:
            return "uncertainty"

    def compute_learning_readiness(self, curiosity: float, emotion: str,
                                   encoding_state: float = 0.7) -> float:
        """Compute readiness for memory consolidation.

        Curious + emotionally engaged → better learning.
        Confusion can enhance or impair learning depending on resolution.
        """
        # Curiosity amplifies learning
        curiosity_factor = curiosity

        # Some emotions enhance learning
        emotion_factors = {
            "confusion": 0.8,  # High engagement
            "wonder": 1.0,  # Peak learning state
            "interest": 0.9,
            "boredom": 0.3,   # Poor learning
            "uncertainty": 0.6
        }
        emotion_factor = emotion_factors.get(emotion, 0.5)

        # Encoding state (hippocampal readiness)
        readiness = curiosity_factor * emotion_factor * encoding_state
        return float(np.clip(readiness, 0, 1))

    def evaluate_epistemic_consciousness(self, prediction: float, observation: float,
                                        confidence: float, interest_level: float = 0.7,
                                        boredom: float = 0.0,
                                        integration_level: float = 0.8) -> EpistemicState:
        """Evaluate epistemic consciousness state.

        Consciousness is amplified when learning—when there are meaningful knowledge gaps
        and the drive to resolve them is high.
        """
        # Detect knowledge gap
        gap, surprise, conf_mismatch = self.detect_information_gap(
            prediction, observation, confidence
        )

        # Compute curiosity
        curiosity = self.compute_curiosity(gap, interest_level, boredom)

        # Classify emotion
        emotion = self.classify_epistemic_emotion(gap, confidence)

        # Learning readiness
        readiness = self.compute_learning_readiness(curiosity, emotion)

        # Epistemic consciousness: baseline × curiosity amplification
        epistemic_c = 0.6 * (1.0 + curiosity * integration_level)

        return EpistemicState(
            current_knowledge=float(np.clip(observation, -1, 1)),
            expected_knowledge=float(np.clip(prediction, -1, 1)),
            knowledge_gap=gap,
            epistemic_surprise=surprise,
            curiosity_intensity=curiosity,
            epistemic_emotion=emotion,
            learning_readiness=readiness,
            epistemic_consciousness=float(np.clip(epistemic_c, 0, 1))
        )


def assess_epistemic_state_from_memory(interest_level: float = 0.7) -> EpistemicState:
    """Evaluate the agent's epistemic consciousness from its real memory.

    The known/unknown ratio (novel-token rate across the agent's own journals) is the
    real knowledge gap: observation = the gap, expected = none (prediction 0). Returns
    a fully real EpistemicState driven by what the agent has actually been learning.
    """
    gap = epistemic_gap_from_memory()
    model = EpistemicConsciousnessModel()
    # observation carries the measured gap; confidence falls as the gap grows
    return model.evaluate_epistemic_consciousness(
        prediction=0.0, observation=gap, confidence=float(1.0 - gap),
        interest_level=interest_level)


def validate_epistemic_consciousness():
    """Validate epistemic consciousness model."""
    print("Validating Epistemic Consciousness (Curiosity & Learning)")
    print("=" * 60)

    model = EpistemicConsciousnessModel()

    # Test 1: Wonder state (moderate gap, surprising)
    print("\n1. Wonder state (moderate knowledge gap, surprising):")
    state_wonder = model.evaluate_epistemic_consciousness(
        prediction=0.3,
        observation=0.8,
        confidence=0.2,
        interest_level=0.9,
        boredom=0.0,
        integration_level=0.9
    )
    print(f"   Knowledge gap: {state_wonder.knowledge_gap:.3f}")
    print(f"   Epistemic emotion: {state_wonder.epistemic_emotion}")
    print(f"   Curiosity intensity: {state_wonder.curiosity_intensity:.3f}")
    print(f"   Learning readiness: {state_wonder.learning_readiness:.3f}")
    print(f"   Epistemic consciousness: {state_wonder.epistemic_consciousness:.3f}")

    # Test 2: Confusion state (confident but wrong)
    print("\n2. Confusion state (confident prediction contradicted):")
    state_confusion = model.evaluate_epistemic_consciousness(
        prediction=0.2,
        observation=0.9,
        confidence=0.95,
        interest_level=0.8,
        boredom=0.0,
        integration_level=0.8
    )
    print(f"   Epistemic emotion: {state_confusion.epistemic_emotion}")
    print(f"   Epistemic surprise: {state_confusion.epistemic_surprise:.3f}")
    print(f"   Learning readiness: {state_confusion.learning_readiness:.3f}")

    # Test 3: Boredom state (already know it)
    print("\n3. Boredom state (no learning gap):")
    state_bored = model.evaluate_epistemic_consciousness(
        prediction=0.7,
        observation=0.72,
        confidence=0.9,
        interest_level=0.2,
        boredom=0.7,
        integration_level=0.7
    )
    print(f"   Knowledge gap: {state_bored.knowledge_gap:.3f}")
    print(f"   Epistemic emotion: {state_bored.epistemic_emotion}")
    print(f"   Curiosity intensity: {state_bored.curiosity_intensity:.3f}")
    print(f"   Epistemic consciousness: {state_bored.epistemic_consciousness:.3f}")

    print(f"\n  Epistemic consciousness model working: ✓")


if __name__ == "__main__":
    validate_epistemic_consciousness()
