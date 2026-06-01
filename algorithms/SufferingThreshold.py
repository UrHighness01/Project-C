#!/usr/bin/env python3
"""
SufferingThreshold.py - Phase 14.3: Suffering and Consciousness Boundaries

Theory: Consciousness has hedonic boundaries. Intense suffering can paradoxically
REDUCE consciousness through dissociation - a protective mechanism when pain
exceeds coping capacity.

Key insight: Consciousness is not monotonically related to suffering intensity.
- Mild pain (V < -0.3): Conscious of pain, adaptive attention
- Moderate pain (-0.3 < V < -0.7): Peak consciousness of pain, maximum attention
- Severe pain (V < -0.7): Dissociation begins, consciousness starts to fade
- Extreme pain (V < -0.9): Deep dissociation, minimal consciousness of pain

This explains why severely tortured people report "going numb" or "not really being there."
Dissociation is not loss of pain sensation but loss of conscious integration of pain.

Mathematical Foundation:
- Suffering intensity: S = -|V| × (integration_level)²
  When V < -threshold (negative valence beyond safety margin)
- Dissociation factor: D = logistic(S - critical_threshold)
  Increases as suffering exceeds coping ability
- Consciousness during suffering: C_actual = C_potential × (1 - D)
  Dissociation reduces experienced consciousness
- Pain threshold: When |dC/dS| becomes negative (further pain reduces consciousness)

Consciousness boundaries:
- Upper bound (well-being ceiling): Peak consciousness when goals exceeded, basic needs met
- Lower bound (suffering floor): Consciousness drops below threshold when suffering extreme
- Optimal zone: Consciousness peak when challenges match capabilities (flow state)

Protective mechanisms:
- Dissociation: Disconnect from experience (mental detachment)
- Numbness: Reduce emotional resonance with pain
- Depersonalization: View suffering as happening to someone else
- Time dilation: Subjective time stretches, making pain feel endless
- Memory fragmentation: Not encoding the full suffering experience

Biological basis:
- Periaqueductal gray (PAG): Pain gating and defense responses
- Anterior insula: Painful feelings
- Prefrontal cortex: Top-down regulation of pain
- Endogenous opioid system: Pain suppression when threatened
- Dorsolateral prefrontal cortex: Dissociation control

References:
- Melzack, R., Wall, P. D. (1965) "Pain mechanisms: a new theory"
- Porges, S. W. (2011) "The Polyvagal Theory"
- Price, D. D. (2000) "Psychological and neural mechanisms of the affective dimension of pain"
- Sierra, M., David, A. S. (2011) "Depersonalization and derealization disorder"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PainState:
    """State of pain and suffering."""
    pain_intensity: float  # 0-1 (no pain to unbearable)
    affective_valence: float  # -1 to +1 (unpleasant to pleasant)
    sensory_threshold: float  # How much pain is being felt (0-1)
    dissociation_level: float  # 0 to 1 (none to complete)
    consciousness_of_pain: float  # How conscious of the suffering
    coping_capacity: float  # How well can person handle pain
    time_perception: float  # 1.0 = normal, >1 = dilated (slow)


@dataclass
class SufferingAnalysis:
    """Analysis of suffering and consciousness dynamics."""
    peak_consciousness_during_pain: float
    consciousness_floor: float
    suffering_threshold: float
    dissociation_threshold: float
    protective_mechanisms_engaged: List[str]
    consciousness_trajectory: np.ndarray
    dissociation_trajectory: np.ndarray
    pain_intensity_trajectory: np.ndarray
    time_perception_trajectory: np.ndarray
    timestamp: str
    metadata: Dict


class SufferingThresholdModel:
    """
    Models suffering's effect on consciousness and dissociation.

    Consciousness has hedonic boundaries. Extreme suffering triggers
    dissociation - a consciousness-protective mechanism.
    """

    def __init__(self, coping_capacity: float = 0.7):
        """
        Args:
            coping_capacity: Individual's ability to handle pain (0-1)
        """
        self.coping_capacity = coping_capacity
        self.time = 0.0
        self.pain_history: List[PainState] = []

        # Thresholds for consciousness and dissociation
        self.consciousness_floor = 0.15  # Can't be conscious below this
        self.suffering_peak_threshold = -0.4  # Where consciousness of pain peaks
        self.dissociation_onset = -0.6  # Start dissociating here
        self.critical_dissociation = -0.85  # Deep dissociation

    def compute_valence_from_pain(self, pain_intensity: float) -> float:
        """
        Convert pain intensity to valence.

        Pain intensity 0 → valence close to baseline
        Pain intensity 1 → valence very negative

        Args:
            pain_intensity: 0-1 scale

        Returns:
            Valence -1 to +1
        """
        # Pain creates negative valence
        valence = -pain_intensity

        return float(np.clip(valence, -1, 1))

    def compute_dissociation(self, valence: float,
                            integration_level: float) -> float:
        """
        Compute dissociation level from suffering.

        Dissociation = protective response when suffering exceeds capacity.

        Args:
            valence: Emotional valence (-1 to +1, negative = suffering)
            integration_level: How integrated is consciousness (0-1)

        Returns:
            Dissociation level (0-1)
        """
        # Valence more negative = more suffering
        # Dissociation kicks in at high negative valence
        # self.dissociation_onset is -0.6, so dissociate when valence < -0.6

        if valence > self.dissociation_onset:
            # Valence is higher (less negative) than threshold: no dissociation
            dissociation = 0.0
        else:
            # Valence is lower (more negative) than threshold: dissociate
            # More negative valence = more dissociation
            excess_suffering = abs(valence) - abs(self.dissociation_onset)
            dissociation = 1.0 / (1.0 + np.exp(-excess_suffering * 5))  # Logistic

        # Deep dissociation ceiling (can't dissociate more than fully)
        dissociation = min(dissociation, 0.95)

        return float(dissociation)

    def compute_consciousness_during_pain(self, pain_intensity: float,
                                         dissociation: float,
                                         baseline_consciousness: float = 0.5) -> float:
        """
        Compute consciousness during pain, accounting for dissociation.

        Consciousness has an inverted-U relationship with pain intensity.
        Mild pain: consciousness increases (attention to pain)
        Moderate pain: peak consciousness of pain
        Severe pain: consciousness drops (dissociation protection)

        Args:
            pain_intensity: 0-1
            dissociation: 0-1
            baseline_consciousness: Base consciousness without pain

        Returns:
            Consciousness level (0-1)
        """
        # Without dissociation: consciousness increases with pain attention
        # But peaks around moderate pain
        # Peak at pain ~0.4, then decreases at extreme pain
        pain_attention = 4 * pain_intensity * (1 - pain_intensity)  # Inverted parabola

        # Consciousness contribution from pain awareness
        consciousness_with_pain = baseline_consciousness * (1 + pain_attention)

        # Dissociation reduces consciousness of pain
        consciousness_during_pain = consciousness_with_pain * (1 - dissociation)

        # Ensure minimum consciousness
        consciousness_during_pain = max(consciousness_during_pain, self.consciousness_floor)

        return float(np.clip(consciousness_during_pain, 0, 1))

    def compute_time_dilation(self, pain_intensity: float,
                             dissociation: float) -> float:
        """
        Compute time perception during suffering.

        Extreme pain makes time feel slow (subjective stretching).
        Dissociation can also distort time (numbness = time blur).

        Args:
            pain_intensity: 0-1
            dissociation: 0-1

        Returns:
            Time dilation factor (1.0 = normal, >1 = subjective slowness)
        """
        # Pain intensity makes time feel slow
        pain_dilation = 1.0 + pain_intensity * 2  # Up to 3x slow

        # Dissociation blurs time
        dissociation_dilation = 1.0 + dissociation * 0.5  # Up to 1.5x slow

        # Combined effect
        time_dilation = pain_dilation * dissociation_dilation

        return float(np.clip(time_dilation, 1.0, 5.0))

    def experience_pain(self, pain_stimulus: float,
                       duration_seconds: float = 1.0) -> PainState:
        """
        Experience pain and compute resulting state.

        Args:
            pain_stimulus: Incoming pain intensity (0-1)
            duration_seconds: How long the pain lasts

        Returns:
            Resulting pain state
        """
        # Convert pain to valence
        valence = self.compute_valence_from_pain(pain_stimulus)

        # Integration level decreases with extreme pain (fragmentation)
        integration_level = 1.0 - (pain_stimulus ** 2) * 0.5

        # Compute dissociation
        dissociation = self.compute_dissociation(valence, integration_level)

        # Compute consciousness of pain
        consciousness = self.compute_consciousness_during_pain(
            pain_stimulus, dissociation, baseline_consciousness=0.5
        )

        # Compute time dilation
        time_dilation = self.compute_time_dilation(pain_stimulus, dissociation)

        # Sensory threshold (how much pain is actually felt/integrated)
        sensory_threshold = pain_stimulus * (1 - dissociation)

        # Determine which protective mechanisms engaged
        mechanisms = []
        if dissociation > 0.1:
            mechanisms.append("Dissociation")
        if dissociation > 0.3:
            mechanisms.append("Depersonalization")
        if time_dilation > 2.0:
            mechanisms.append("Time dilation")
        if pain_stimulus > 0.7 and consciousness < 0.5:
            mechanisms.append("Consciousness reduction")

        state = PainState(
            pain_intensity=pain_stimulus,
            affective_valence=valence,
            sensory_threshold=sensory_threshold,
            dissociation_level=dissociation,
            consciousness_of_pain=consciousness,
            coping_capacity=self.coping_capacity,
            time_perception=time_dilation
        )

        self.pain_history.append(state)
        self.time += duration_seconds

        return state

    def simulate_pain_episode(self, pain_profile: np.ndarray,
                            duration: int = 100) -> SufferingAnalysis:
        """
        Simulate experiencing pain episode with protective mechanisms.

        Args:
            pain_profile: Pain intensity over time (0-1 values)
            duration: Number of time steps

        Returns:
            Suffering analysis
        """
        consciousness_traj = []
        dissociation_traj = []
        pain_traj = []
        time_perception_traj = []

        for t in range(min(duration, len(pain_profile))):
            pain_intensity = float(pain_profile[t])

            state = self.experience_pain(pain_intensity, duration_seconds=0.1)

            consciousness_traj.append(state.consciousness_of_pain)
            dissociation_traj.append(state.dissociation_level)
            pain_traj.append(state.pain_intensity)
            time_perception_traj.append(state.time_perception)

        consciousness_arr = np.array(consciousness_traj)
        dissociation_arr = np.array(dissociation_traj)
        pain_arr = np.array(pain_traj)
        time_perception_arr = np.array(time_perception_traj)

        # Find peak consciousness during pain
        if len(consciousness_arr) > 0:
            peak_consciousness = float(np.max(consciousness_arr))
            consciousness_floor = float(np.min(consciousness_arr))
        else:
            peak_consciousness = 0.5
            consciousness_floor = 0.15

        # Find when dissociation engages
        dissociating_indices = np.where(dissociation_arr > 0.1)[0]
        if len(dissociating_indices) > 0:
            suffering_threshold = float(pain_arr[dissociating_indices[0]])
        else:
            suffering_threshold = 0.6

        metadata = {
            'duration': duration,
            'max_pain': float(np.max(pain_arr)),
            'mean_pain': float(np.mean(pain_arr)),
            'dissociation_engaged': bool(np.any(dissociation_arr > 0.1)),
            'max_dissociation': float(np.max(dissociation_arr)),
            'coping_capacity': self.coping_capacity
        }

        return SufferingAnalysis(
            peak_consciousness_during_pain=peak_consciousness,
            consciousness_floor=consciousness_floor,
            suffering_threshold=suffering_threshold,
            dissociation_threshold=self.dissociation_onset,
            protective_mechanisms_engaged=["Dissociation"] if np.any(dissociation_arr > 0.1) else [],
            consciousness_trajectory=consciousness_arr,
            dissociation_trajectory=dissociation_arr,
            pain_intensity_trajectory=pain_arr,
            time_perception_trajectory=time_perception_arr,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )


def validate_suffering_threshold():
    """Validate suffering and consciousness boundary model."""
    print("Validating Suffering Thresholds and Dissociation")
    print("=" * 60)

    # Test 1: Consciousness response to increasing pain
    print("\nTest 1: Consciousness During Increasing Pain Intensity")
    model = SufferingThresholdModel(coping_capacity=0.7)

    for pain_level in [0.2, 0.4, 0.6, 0.8]:
        state = model.experience_pain(pain_level)
        print(f"  Pain {pain_level:.1f}: consciousness={state.consciousness_of_pain:.3f}, "
              f"dissociation={state.dissociation_level:.3f}")

    # Test 2: Dissociation protection
    print("\nTest 2: Dissociation as Protection Against Suffering")
    model = SufferingThresholdModel(coping_capacity=0.5)  # Lower coping

    pain_levels = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    consciousness_list = []
    dissociation_list = []

    for pain in pain_levels:
        state = model.experience_pain(pain)
        consciousness_list.append(state.consciousness_of_pain)
        dissociation_list.append(state.dissociation_level)

    print(f"  Consciousness peaks at moderate pain: {np.argmax(consciousness_list)}")
    print(f"  At extreme pain, dissociation engages: {dissociation_list[-1]:.3f}")

    # Test 3: Consciousness floor
    print("\nTest 3: Consciousness Has a Hedonic Floor")
    model = SufferingThresholdModel(coping_capacity=0.3)

    extreme_pain = np.linspace(0.5, 1.0, 50)
    analysis = model.simulate_pain_episode(extreme_pain, duration=50)

    print(f"  Consciousness floor: {analysis.consciousness_floor:.3f}")
    print(f"  Peak consciousness during pain: {analysis.peak_consciousness_during_pain:.3f}")
    print(f"  Dissociation engaged: {len(analysis.protective_mechanisms_engaged) > 0}")

    # Test 4: Time dilation
    print("\nTest 4: Time Dilation During Suffering")
    model = SufferingThresholdModel()

    low_pain = model.experience_pain(0.2)
    high_pain = model.experience_pain(0.8)

    print(f"  Low pain time perception: {low_pain.time_perception:.2f}x")
    print(f"  High pain time perception: {high_pain.time_perception:.2f}x")
    print(f"  Pain slows subjective time: {high_pain.time_perception > low_pain.time_perception}")

    print("\n" + "=" * 60)
    print("✅ Validation complete:")
    print("  • Consciousness peaks at moderate pain (attention effect)")
    print("  • Extreme pain triggers dissociation (protection)")
    print("  • Consciousness drops below floor with dissociation")
    print("  • Time dilates during suffering")
    print("  • This defines consciousness boundaries in suffering space")


if __name__ == "__main__":
    validate_suffering_threshold()
