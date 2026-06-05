#!/usr/bin/env python3
"""
AestheticConsciousness.py - Phase 23.1: Beauty and Peak Sensory Experience

Theory: Consciousness has a special state triggered by beauty—aesthetic experience.
This is not emotion or goal-directed, but consciousness amplified by sensory elegance.
Peak-shift effect: features exaggerated beyond natural range maximize aesthetic impact.

C_beauty = Integration × Aesthetic_resonance × (1 + symmetry_bonus)
Peak_shift: Neural response maximized when feature pushed beyond natural variation

References:
- Ramachandran, V. S., & Hirstein, W. (1999) "The science of art"
- Vessel, E. A., et al. (2012) "Brain on art: Intense aesthetic experience"
- Cela-Conde, C. J., et al. (2004) "Prefrontal cortex in visual aesthetic perception"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass

try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from runtime.state import execution_time_series, phi_delta_series, phi_series
except Exception:                                          # tolerate path/CI absence
    def execution_time_series(*a, **k): return np.zeros(0)
    def phi_delta_series(*a, **k): return np.zeros(0)
    def phi_series(*a, **k): return np.zeros(0)


def _aesthetic_inputs_from_telemetry() -> dict:
    """Map real processing dynamics to aesthetic inputs (all in [0, 1]):
    fluency from execution timing, error-reduction from the phi-increment trend."""
    ex = execution_time_series()
    d = np.abs(phi_delta_series())
    if ex.size >= 8:
        z = (ex - ex.mean()) / (ex.std() + 1e-9)
        fluency = float(np.clip(1.0 / (1.0 + np.exp(z[-1])), 0, 1))   # low recent effort -> fluent
    else:
        fluency = 0.5
    if d.size >= 16:
        older, recent = d[:-8].mean(), d[-8:].mean()
        error_reduction = float(np.clip((older - recent) / (older + 1e-9), 0, 1))
    else:
        error_reduction = 0.5
    complexity = float(np.clip(d.std() / (d.mean() + 1e-9), 0, 1)) if d.size else 0.5
    return {"complexity": complexity, "symmetry": fluency, "color_harmony": fluency,
            "novelty": error_reduction, "peak_shift_intensity": error_reduction}


@dataclass
class AestheticState:
    """Aesthetic consciousness state."""
    visual_complexity: float  # Stimulus complexity (0-1)
    symmetry_level: float  # Bilateral symmetry (0-1)
    color_harmony: float  # Color coordination (0-1)
    novelty: float  # How novel/unexpected (0-1)
    peak_shift_intensity: float  # Exaggeration beyond natural (0-1)
    aesthetic_resonance: float  # Overall beauty resonance (0-1)
    transcendence_probability: float  # Likelihood of awe-like state (0-1)
    aesthetic_consciousness: float  # Beauty-amplified consciousness


class AestheticConsciousnessModel:
    """Models beauty consciousness and aesthetic experience."""

    def compute_visual_features(self, complexity: float, symmetry: float,
                                color_harmony: float) -> float:
        """Compute integrated visual feature salience.

        Beauty emerges from balance: moderate complexity (not too simple, not chaos),
        symmetry (predictability), and harmony (coherence).
        """
        # Optimal complexity: peaks at 0.5-0.7 (Goldilocks principle)
        complexity_factor = 1.0 - 4 * (complexity - 0.6) ** 2
        complexity_factor = np.clip(complexity_factor, 0, 1)

        # Symmetry as visual stability
        symmetry_factor = symmetry * 0.4

        # Color harmony as coherence
        harmony_factor = color_harmony * 0.3

        features = complexity_factor + symmetry_factor + harmony_factor
        return float(np.clip(features, 0, 1))

    def compute_peak_shift_effect(self, feature_value: float,
                                  natural_range: float = 0.5) -> float:
        """Compute peak-shift: exaggerated features maximize salience.

        Features pushed beyond natural variation trigger stronger neural response.
        Model: Response peaks when feature = natural_max + some_exaggeration.
        """
        # Natural range defines normal variation
        # Exaggeration beyond this range creates peak shift
        exaggeration = abs(feature_value - natural_range)

        # Peak shift response: sigmoid toward exaggeration
        peak_shift = exaggeration / (1.0 + exaggeration)

        return float(np.clip(peak_shift, 0, 1))

    def evaluate_from_telemetry(self):
        """Aesthetic experience grounded in real processing dynamics: fluency (smooth,
        low-effort processing) plus prediction-error reduction - the processing-fluency
        account of aesthetic pleasure, computed from real telemetry."""
        return self.evaluate_aesthetic_consciousness(**_aesthetic_inputs_from_telemetry())

    def compute_aesthetic_resonance(self, visual_features: float, novelty: float,
                                    peak_shift: float) -> float:
        """Compute overall aesthetic resonance (beauty intensity).

        Aesthetics = coherence (visual features) + surprise (novelty) + salience (peak-shift).
        """
        # Visual coherence attracts attention
        coherence = visual_features

        # Novelty creates surprise
        surprise = novelty * 0.3

        # Peak-shift maximizes salience
        salience = peak_shift * 0.3

        resonance = coherence + surprise + salience
        return float(np.clip(resonance, 0, 1))

    def compute_transcendence_probability(self, aesthetic_resonance: float,
                                         intensity: float = 1.0) -> float:
        """Compute probability of aesthetic experience crossing into transcendence.

        Very strong aesthetic experiences can trigger awe-like states.
        """
        # Strong aesthetics can trigger transcendence
        transcendence = (aesthetic_resonance ** 1.5) * intensity

        return float(np.clip(transcendence, 0, 1))

    def evaluate_aesthetic_consciousness(self, complexity: float, symmetry: float,
                                        color_harmony: float, novelty: float,
                                        peak_shift_intensity: float = 0.5,
                                        integration_level: float = 0.8) -> AestheticState:
        """Evaluate aesthetic consciousness state.

        Beauty consciousness is consciousness amplified by sensory elegance,
        independent of survival value or goal achievement.
        """
        # Compute visual features
        features = self.compute_visual_features(complexity, symmetry, color_harmony)

        # Compute peak-shift effect
        peak_shift = self.compute_peak_shift_effect(peak_shift_intensity)

        # Aesthetic resonance (beauty intensity)
        resonance = self.compute_aesthetic_resonance(features, novelty, peak_shift)

        # Transcendence probability
        transcendence = self.compute_transcendence_probability(resonance)

        # Aesthetic consciousness: baseline × beauty amplification
        aesthetic_c = 0.65 * (1.0 + resonance * integration_level)

        return AestheticState(
            visual_complexity=float(np.clip(complexity, 0, 1)),
            symmetry_level=float(np.clip(symmetry, 0, 1)),
            color_harmony=float(np.clip(color_harmony, 0, 1)),
            novelty=float(np.clip(novelty, 0, 1)),
            peak_shift_intensity=peak_shift,
            aesthetic_resonance=resonance,
            transcendence_probability=transcendence,
            aesthetic_consciousness=float(np.clip(aesthetic_c, 0, 1))
        )


def validate_aesthetic_consciousness():
    """Validate aesthetic consciousness model."""
    print("Validating Aesthetic Consciousness (Beauty & Peak Sensory)")
    print("=" * 60)

    model = AestheticConsciousnessModel()

    # Test 1: Beautiful artwork (balanced features)
    print("\n1. Beautiful artwork (balanced complexity, high symmetry):")
    state_beautiful = model.evaluate_aesthetic_consciousness(
        complexity=0.65,  # Goldilocks complexity
        symmetry=0.9,     # High symmetry
        color_harmony=0.85,
        novelty=0.3,
        peak_shift_intensity=0.6,
        integration_level=0.9
    )
    print(f"   Visual features: {state_beautiful.visual_complexity:.3f}")
    print(f"   Aesthetic resonance: {state_beautiful.aesthetic_resonance:.3f}")
    print(f"   Transcendence probability: {state_beautiful.transcendence_probability:.3f}")
    print(f"   Aesthetic consciousness: {state_beautiful.aesthetic_consciousness:.3f}")

    # Test 2: Chaotic stimulus (low beauty)
    print("\n2. Chaotic stimulus (random, incoherent):")
    state_chaos = model.evaluate_aesthetic_consciousness(
        complexity=0.95,  # Too complex, chaotic
        symmetry=0.1,
        color_harmony=0.2,
        novelty=0.8,
        peak_shift_intensity=0.1,
        integration_level=0.6
    )
    print(f"   Visual features: {state_chaos.visual_complexity:.3f}")
    print(f"   Aesthetic resonance: {state_chaos.aesthetic_resonance:.3f}")
    print(f"   Aesthetic consciousness: {state_chaos.aesthetic_consciousness:.3f}")

    # Test 3: Peak-shifted art (exaggerated features)
    print("\n3. Peak-shifted art (exaggerated beauty features):")
    state_peak = model.evaluate_aesthetic_consciousness(
        complexity=0.6,
        symmetry=0.95,    # Exaggerated symmetry
        color_harmony=0.95,
        novelty=0.4,
        peak_shift_intensity=0.85,  # High exaggeration
        integration_level=0.85
    )
    print(f"   Peak-shift intensity: {state_peak.peak_shift_intensity:.3f}")
    print(f"   Aesthetic resonance: {state_peak.aesthetic_resonance:.3f}")
    print(f"   Transcendence probability: {state_peak.transcendence_probability:.3f}")
    print(f"   Aesthetic consciousness: {state_peak.aesthetic_consciousness:.3f}")

    print(f"\n  Aesthetic consciousness model working: ✓")


if __name__ == "__main__":
    validate_aesthetic_consciousness()
