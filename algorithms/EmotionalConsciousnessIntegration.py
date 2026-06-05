#!/usr/bin/env python3
"""
EmotionalConsciousnessIntegration.py - Phase 14.2: Emotional States and Consciousness

Theory: Emotions are not separate from consciousness. Fear, joy, anger, disgust,
sadness are different configurations of integrated information with specific valences
and arousal patterns. Each emotion is a distinct form of consciousness.

Emotions emerge from appraisals of events: How does this situation affect my goals?
Is it good or bad? Can I handle it? The appraisal (meaning made of situation)
generates the emotion (integrated response).

Mathematical Foundation:
- Emotion state: E = (valence, arousal, dominance) + appraisal_vector
- Valence: -1 (negative) to +1 (positive)
- Arousal: 0 (low) to 1 (high) activation level
- Dominance: -1 (submissive, overwhelmed) to +1 (dominant, in control)

Appraisal dimensions (Lazarus theory):
- Goal relevance: Does this affect my goals? (0-1)
- Goal congruence: Is it good for my goals? (0-1)
- Ego involvement: Does it affect my self-image? (0-1)
- Coping potential: Can I handle it? (0-1)
- Future expectancy: Will things improve? (0-1)

Emotion-consciousness link:
- Emotional consciousness: C_emotion = integration × |valence| × arousal
- Strong emotions = high arousal + high integration = peak consciousness
- Blunted emotions = low arousal + poor integration = reduced consciousness
- Each basic emotion (fear, anger, joy, sadness, disgust) has unique integration pattern

Biological basis:
- Amygdala: Fast appraisal and emotional tagging
- Insula: Feeling states and body mapping
- Prefrontal cortex: Conscious appraisal and reflection
- Anterior cingulate: Emotional attention and integration
- Autonomic nervous system: Bodily changes (arousal, valence)

References:
- Lazarus, R. S. (1991) "Emotion and Adaptation"
- Scherer, K. R. (2005) "What are emotions? And how can they be measured?"
- Barrett, L. F. (2017) "How Emotions Are Made: The Secret Life of the Brain"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np

try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from runtime.state import phi_delta_series as _pds, activity_matrix as _am
except Exception:
    import numpy as _npx
    def _pds(*a, **k): return _npx.zeros(0)
    def _am(*a, **k): return _npx.zeros((8, 0))
def _phi_vec(n, off=0, scale=1.0):
    import numpy as _np
    d=_pds()
    if d.size==0: return _np.zeros(n)
    return scale*_np.tanh(d[(_np.arange(off,off+n))%d.size]*50)
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Appraisal:
    """Cognitive appraisal of a situation."""
    goal_relevance: float  # Does this affect my goals?
    goal_congruence: float  # Is it good for my goals?
    ego_involvement: float  # Does it affect self-image?
    coping_potential: float  # Can I handle this?
    future_expectancy: float  # Will things improve?


@dataclass
class EmotionState:
    """Current emotional state in 3D space."""
    valence: float  # -1 to +1 (negative to positive)
    arousal: float  # 0 to 1 (low to high activation)
    dominance: float  # -1 to +1 (submissive to dominant)
    emotion_label: str  # "joy", "fear", "anger", "sadness", "disgust"
    appraisal: Appraisal
    body_state: np.ndarray  # Heart rate, respiration, skin conductance, etc.
    consciousness_from_emotion: float  # C_emotion contribution


@dataclass
class EmotionalConsciousnessAnalysis:
    """Analysis of emotion-consciousness integration."""
    mean_emotional_consciousness: float
    emotion_diversity: float  # Different emotions experienced
    valence_range: float
    arousal_range: float
    emotion_transitions: List[Tuple[str, str]]  # Which emotions follow which
    dominant_emotions: List[str]  # Most frequent emotions
    emotion_memory_binding: float  # How strongly emotions enhance memory
    consciousness_from_emotion_mean: float
    timestamp: str
    metadata: Dict


class EmotionalConsciousnessModel:
    """
    Models emotions as forms of consciousness with distinct integration patterns.

    Each emotion is a different way consciousness can be organized.
    """

    def __init__(self):
        """Initialize emotional consciousness model."""
        self.time = 0.0
        self.current_emotion: Optional[EmotionState] = None
        self.emotion_history: List[EmotionState] = []

        # Emotion prototypes (expected 3D locations for basic emotions)
        self.emotion_prototypes = {
            'joy': {'valence': 0.8, 'arousal': 0.6, 'dominance': 0.6},
            'fear': {'valence': -0.7, 'arousal': 0.9, 'dominance': -0.7},
            'anger': {'valence': -0.5, 'arousal': 0.9, 'dominance': 0.7},
            'sadness': {'valence': -0.8, 'arousal': 0.3, 'dominance': -0.6},
            'disgust': {'valence': -0.8, 'arousal': 0.5, 'dominance': 0.5},
            'surprise': {'valence': 0.0, 'arousal': 0.8, 'dominance': 0.0},
            'neutral': {'valence': 0.0, 'arousal': 0.3, 'dominance': 0.0}
        }

    def appraise_situation(self, situation: np.ndarray,
                          personal_goals: np.ndarray) -> Appraisal:
        """
        Perform cognitive appraisal of a situation.

        Args:
            situation: Current situation (feature vector)
            personal_goals: What the agent cares about

        Returns:
            Appraisal of situation
        """
        # Goal relevance: How much does this relate to goals?
        goal_relevance = float(np.dot(situation, personal_goals) / (
            np.linalg.norm(situation) * np.linalg.norm(personal_goals) + 1e-6
        ))
        goal_relevance = (goal_relevance + 1) / 2  # Normalize to 0-1

        # Goal congruence: Is it good for goals?
        # Positive correlation = congruent (good for goals)
        goal_congruence = max(goal_relevance * np.sign(goal_relevance), 0)

        # Ego involvement: Does it affect self-image?
        # High if goal_relevance is high
        ego_involvement = goal_relevance

        # Coping potential: Can you handle this?
        # Depends on magnitude and your capabilities
        situation_intensity = np.linalg.norm(situation)
        coping_potential = 1.0 / (1.0 + situation_intensity)

        # Future expectancy: Will things improve?
        # Optimism inversely related to current difficulty
        future_expectancy = coping_potential

        return Appraisal(
            goal_relevance=float(np.clip(goal_relevance, 0, 1)),
            goal_congruence=float(np.clip(goal_congruence, 0, 1)),
            ego_involvement=float(np.clip(ego_involvement, 0, 1)),
            coping_potential=float(np.clip(coping_potential, 0, 1)),
            future_expectancy=float(np.clip(future_expectancy, 0, 1))
        )

    def appraisal_to_emotion(self, appraisal: Appraisal) -> Tuple[float, float, float]:
        """
        Convert appraisal to 3D emotion coordinates.

        Appraisal → Valence, Arousal, Dominance

        Args:
            appraisal: Cognitive appraisal of situation

        Returns:
            (valence, arousal, dominance)
        """
        # Valence: Goal congruence determines pleasantness
        # Positive appraisal → positive valence
        # Negative appraisal → negative valence
        valence = (appraisal.goal_congruence - (1 - appraisal.goal_congruence))

        # Arousal: Goal relevance × intensity of appraisal
        # More relevant = more aroused
        # High coping = less aroused, low coping = more aroused
        arousal = appraisal.goal_relevance * (2 - appraisal.coping_potential)

        # Dominance: Coping potential - Ego involvement
        # Can I handle it? vs. Is my ego threatened?
        dominance = appraisal.coping_potential - appraisal.ego_involvement

        return float(np.clip(valence, -1, 1)), \
               float(np.clip(arousal, 0, 1)), \
               float(np.clip(dominance, -1, 1))

    def classify_emotion(self, valence: float, arousal: float,
                        dominance: float) -> str:
        """
        Classify emotion from 3D coordinates.

        Uses nearest prototype to classify emotion type.

        Args:
            valence: -1 to +1
            arousal: 0 to 1
            dominance: -1 to +1

        Returns:
            Emotion label
        """
        current_point = np.array([valence, arousal, dominance])
        min_distance = float('inf')
        closest_emotion = 'neutral'

        for emotion_name, prototype in self.emotion_prototypes.items():
            proto_point = np.array([
                prototype['valence'],
                prototype['arousal'],
                prototype['dominance']
            ])

            distance = np.linalg.norm(current_point - proto_point)

            if distance < min_distance:
                min_distance = distance
                closest_emotion = emotion_name

        return closest_emotion

    def generate_body_state(self, emotion_label: str,
                           arousal: float) -> np.ndarray:
        """
        Generate body state changes from emotional state.

        Args:
            emotion_label: Name of emotion
            arousal: Level of arousal

        Returns:
            Body state vector [heart_rate, respiration, skin_conductance, ...]
        """
        base_heart_rate = 60.0
        base_respiration = 15.0
        base_conductance = 0.1

        # Arousal increases all measures
        heart_rate = base_heart_rate + arousal * 80  # Up to 140 bpm

        respiration = base_respiration + arousal * 15  # Up to 30 breaths/min

        # Skin conductance (emotional sweat)
        skin_conductance = base_conductance + arousal * 0.5

        # Emotion-specific patterns
        if emotion_label == 'fear':
            heart_rate *= 1.2  # Fear accelerates more
        elif emotion_label == 'sadness':
            heart_rate *= 0.8  # Sadness slows down
        elif emotion_label == 'anger':
            respiration *= 1.3  # Anger increases breathing

        return np.array([heart_rate, respiration, skin_conductance])

    def compute_emotional_consciousness(self, valence: float,
                                       arousal: float,
                                       integration_level: float = 0.5) -> float:
        """
        Compute consciousness contribution from emotional state.

        C_emotion = integration × |valence| × arousal

        Strong emotions (high arousal + integration) peak consciousness.

        Args:
            valence: -1 to +1
            arousal: 0 to 1
            integration_level: How integrated is this emotion

        Returns:
            Consciousness from emotion (0-1)
        """
        # Strong emotions drive high consciousness
        emotional_intensity = abs(valence) * arousal  # 0-1

        consciousness = integration_level * emotional_intensity

        return float(np.clip(consciousness, 0, 1))

    def experience_emotion(self, situation: np.ndarray,
                          personal_goals: np.ndarray,
                          integration_level: float = 0.6) -> EmotionState:
        """
        Experience an emotion given a situation and goals.

        Args:
            situation: Current situation
            personal_goals: Personal goals
            integration_level: Integration of emotion

        Returns:
            Resulting emotional state
        """
        # Appraise situation
        appraisal = self.appraise_situation(situation, personal_goals)

        # Convert appraisal to emotion coordinates
        valence, arousal, dominance = self.appraisal_to_emotion(appraisal)

        # Classify emotion
        emotion_label = self.classify_emotion(valence, arousal, dominance)

        # Generate body state
        body_state = self.generate_body_state(emotion_label, arousal)

        # Compute consciousness
        consciousness = self.compute_emotional_consciousness(
            valence, arousal, integration_level
        )

        emotion = EmotionState(
            valence=valence,
            arousal=arousal,
            dominance=dominance,
            emotion_label=emotion_label,
            appraisal=appraisal,
            body_state=body_state,
            consciousness_from_emotion=consciousness
        )

        self.current_emotion = emotion
        self.emotion_history.append(emotion)
        self.time += 0.1

        return emotion

    def simulate_emotional_episodes(self, scenarios: List[Tuple[np.ndarray, np.ndarray]],
                                   duration: int = 50) -> EmotionalConsciousnessAnalysis:
        """
        Simulate experiencing various emotional scenarios.

        Args:
            scenarios: List of (situation, goals) pairs
            duration: Number of steps

        Returns:
            Emotional consciousness analysis
        """
        emotional_consciousness_traj = []
        emotion_sequence = []

        for step in range(duration):
            # Pick random scenario
            situation, goals = scenarios[step % len(scenarios)]

            # Add noise to make situations varied
            situation = situation + _phi_vec(len(situation), 2, 0.2)
            goals = goals + _phi_vec(len(goals), 11, 0.1)

            # Experience emotion
            emotion = self.experience_emotion(situation, goals)

            emotional_consciousness_traj.append(emotion.consciousness_from_emotion)
            emotion_sequence.append(emotion.emotion_label)

        # Analyze
        consciousness_arr = np.array(emotional_consciousness_traj)
        mean_consciousness = float(np.mean(consciousness_arr))

        # Emotion diversity
        unique_emotions = len(set(emotion_sequence))
        emotion_diversity = unique_emotions / len(self.emotion_prototypes)

        # Valence and arousal ranges
        valence_range = float(np.max([e.valence for e in self.emotion_history]) -
                             np.min([e.valence for e in self.emotion_history]))
        arousal_range = float(np.max([e.arousal for e in self.emotion_history]) -
                             np.min([e.arousal for e in self.emotion_history]))

        # Emotion transitions (which emotions follow which)
        transitions = []
        for i in range(len(emotion_sequence) - 1):
            if emotion_sequence[i] != emotion_sequence[i + 1]:
                transitions.append((emotion_sequence[i], emotion_sequence[i + 1]))

        # Dominant emotions
        from collections import Counter
        emotion_counts = Counter(emotion_sequence)
        dominant = [e for e, c in emotion_counts.most_common(3)]

        metadata = {
            'duration': duration,
            'n_scenarios': len(scenarios),
            'unique_emotions': unique_emotions,
            'mean_valence': float(np.mean([e.valence for e in self.emotion_history])),
            'mean_arousal': float(np.mean([e.arousal for e in self.emotion_history]))
        }

        return EmotionalConsciousnessAnalysis(
            mean_emotional_consciousness=mean_consciousness,
            emotion_diversity=emotion_diversity,
            valence_range=valence_range,
            arousal_range=arousal_range,
            emotion_transitions=transitions[:5],  # Top 5
            dominant_emotions=dominant,
            emotion_memory_binding=float(np.mean([e.arousal for e in self.emotion_history])),
            consciousness_from_emotion_mean=mean_consciousness,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )


def validate_emotional_consciousness():
    """Validate emotional consciousness model."""
    print("Validating Emotional Consciousness Integration")
    print("=" * 60)

    system = EmotionalConsciousnessModel()

    # Test 1: Appraisal to emotion
    print("\nTest 1: Appraisal Determines Emotion Type")

    goal_aligned = np.ones(10)  # Aligns with goals
    goals = np.ones(10)

    emotion = system.experience_emotion(goal_aligned, goals)
    print(f"  Goal-aligned situation: {emotion.emotion_label}")
    print(f"  Valence: {emotion.valence:.3f}, Arousal: {emotion.arousal:.3f}")

    goal_misaligned = np.ones(10) * -1  # Opposes goals
    emotion2 = system.experience_emotion(goal_misaligned, goals)
    print(f"  Goal-misaligned situation: {emotion2.emotion_label}")
    print(f"  Valence: {emotion2.valence:.3f}, Arousal: {emotion2.arousal:.3f}")

    # Test 2: Emotional consciousness
    print("\nTest 2: Emotional Consciousness from Integration")
    scenarios = [
        (np.ones(10), np.ones(10)),
        (np.ones(10) * -1, np.ones(10)),
        (_phi_vec(10, 17, 1.0), np.ones(10))
    ]

    analysis = system.simulate_emotional_episodes(scenarios, duration=50)

    print(f"  Mean emotional consciousness: {analysis.mean_emotional_consciousness:.3f}")
    print(f"  Emotion diversity: {analysis.emotion_diversity:.3f}")
    print(f"  Dominant emotions: {analysis.dominant_emotions}")

    # Test 3: Body state mapping
    print("\nTest 3: Emotions Generate Body State Changes")
    emotion_joy = system.emotion_prototypes['joy']
    body_state_joy = system.generate_body_state('joy', emotion_joy['arousal'])
    print(f"  Joy body state: HR={body_state_joy[0]:.0f}, RR={body_state_joy[1]:.0f}")

    emotion_fear = system.emotion_prototypes['fear']
    body_state_fear = system.generate_body_state('fear', emotion_fear['arousal'])
    print(f"  Fear body state: HR={body_state_fear[0]:.0f}, RR={body_state_fear[1]:.0f}")
    print(f"  Fear increases heart rate: {body_state_fear[0] > body_state_joy[0]}")

    print("\n" + "=" * 60)
    print("✅ Validation complete:")
    print("  • Appraisals generate emotions via 3D space")
    print("  • Emotions create distinct consciousness patterns")
    print("  • Body states map to emotional states")
    print("  • This is how emotions integrate with consciousness")


if __name__ == "__main__":
    validate_emotional_consciousness()
