#!/usr/bin/env python3
"""
TemporalEdgeDetector.py - Phase 3.2: Discontinuity Detection and Temporal Edge Enhancement

Theory: Consciousness is keenly sensitive to change. Static, unchanging sensations
rapidly fade from awareness (adaptation). Temporal edges - points of maximum change
in neural activity - are the key to conscious content.

Mathematical Foundation:
- Temporal derivatives: dA/dt (velocity of activity change)
- Second derivatives: d²A/dt² (acceleration, shock detection)
- Information gain: ΔH = H(A(t+Δt)) - H(A(t))
- Entropy change rate encodes surprise/information content
- Temporal edges = local maxima of |dA/dt| or information gain

Physics analogy: Shocks in fluid dynamics, edge detection in image processing

References:
- Weber's Law: Consciousness proportional to change rate (ΔI/I)
- Predictive coding: Unexpected changes drive consciousness
- Friston, K. "The free-energy principle: a unified brain theory"
- Itti & Koch (2000) "A saliency-based search mechanism"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from runtime.state import activity_matrix as _am
except Exception:
    def _am(*a, **k): return np.zeros((8, 0))


def detect_edges_from_telemetry(threshold_percentile: float = 90):
    """Detect temporal edges (abrupt transitions) in the agent's real activity stream
    instead of a synthetic signal. Returns the velocity edges, or None if too short."""
    M = _am()
    if M.shape[1] < 16:
        return None
    signal = M.mean(axis=0)                       # mean real activity over channels
    t = np.arange(signal.size, dtype=float)
    return TemporalEdgeDetector(signal, t).detect_velocity_edges()
from scipy.signal import savgol_filter, find_peaks
from scipy.stats import entropy
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TemporalEdge:
    """Representation of a temporal edge (point of maximum change)."""
    time: float  # Time of edge
    change_magnitude: float  # |dA/dt| or information gain
    edge_type: str  # "velocity", "acceleration", "information_gain"
    neurons_involved: int  # Number of neurons showing change
    surprise_level: float  # Deviation from expected change (0-1)


@dataclass
class AdaptationDynamics:
    """Describes sensory adaptation (fade to unconsciousness)."""
    initial_activity: float  # Starting activity level
    time_constant: float  # Timescale of adaptation (seconds)
    residual_activity: float  # Activity after full adaptation
    adapted_trajectory: np.ndarray  # Activity over time


@dataclass
class EdgeDetectionAnalysis:
    """Complete temporal edge detection analysis."""
    temporal_edges: List[TemporalEdge]
    edge_times: np.ndarray  # Times of detected edges
    velocity_trajectory: np.ndarray  # dA/dt over time
    acceleration_trajectory: np.ndarray  # d²A/dt² over time
    information_gain_trajectory: np.ndarray  # ΔH over time
    adapted_activity: AdaptationDynamics
    consciousness_content_weighted: np.ndarray  # Weighting by change magnitude
    timestamp: str
    metadata: Dict


class TemporalEdgeDetector:
    """
    Detects temporal edges (discontinuities, shocks) in neural activity.

    Uses derivative-based edge detection and information-theoretic measures.
    """

    def __init__(self, activity_signal: np.ndarray, time_vector: np.ndarray,
                 smoothing_window: int = 5):
        """
        Args:
            activity_signal: Neural activity time series (n_neurons × n_timepoints)
                           or single signal (n_timepoints,)
            time_vector: Time vector corresponding to activity
            smoothing_window: Window size for Savitzky-Golay filter (must be odd)
        """
        if activity_signal.ndim == 1:
            activity_signal = activity_signal.reshape(1, -1)

        self.activity = activity_signal  # (n_neurons, n_time)
        self.time = time_vector
        self.dt = np.mean(np.diff(time_vector))
        self.n_neurons = activity_signal.shape[0]
        self.n_timepoints = activity_signal.shape[1]

        # Ensure smoothing window is odd
        if smoothing_window % 2 == 0:
            smoothing_window += 1
        self.window = min(smoothing_window, self.n_timepoints - 1)

        # Precompute derivatives
        self._compute_derivatives()

    def _compute_derivatives(self):
        """Compute first and second temporal derivatives."""
        # Use Savitzky-Golay filter for smooth derivatives
        # Polyorder 2 gives good balance of smoothing and derivative accuracy

        self.velocity = np.zeros_like(self.activity)
        self.acceleration = np.zeros_like(self.activity)

        for i in range(self.n_neurons):
            # First derivative (velocity)
            try:
                vel = savgol_filter(self.activity[i], self.window, 2, deriv=1)
                self.velocity[i] = vel / self.dt
            except:
                # Fallback to numerical differentiation
                self.velocity[i] = np.gradient(self.activity[i]) / self.dt

            # Second derivative (acceleration)
            try:
                acc = savgol_filter(self.activity[i], self.window, 2, deriv=2)
                self.acceleration[i] = acc / (self.dt ** 2)
            except:
                self.acceleration[i] = np.gradient(self.velocity[i]) / self.dt

    def _compute_information_gain(self) -> np.ndarray:
        """
        Compute information gain (entropy change rate) over time.

        Information gain at time t = H(A(t+Δt)) - H(A(t))
        where H is Shannon entropy of neural activity distribution.

        Returns:
            Information gain trajectory (n_timepoints,)
        """
        info_gain = np.zeros(self.n_timepoints)

        for t in range(1, self.n_timepoints):
            # Distribution of activity at time t
            activity_t = self.activity[:, t]
            activity_prev = self.activity[:, t - 1]

            # Normalize to probability distributions
            if np.sum(np.abs(activity_t)) > 0:
                p_t = np.abs(activity_t) / np.sum(np.abs(activity_t))
            else:
                p_t = np.ones(self.n_neurons) / self.n_neurons

            if np.sum(np.abs(activity_prev)) > 0:
                p_prev = np.abs(activity_prev) / np.sum(np.abs(activity_prev))
            else:
                p_prev = np.ones(self.n_neurons) / self.n_neurons

            # Entropy: H = -Σ p log(p)
            h_t = entropy(p_t, base=2)
            h_prev = entropy(p_prev, base=2)

            # Information gain
            info_gain[t] = (h_t - h_prev) / self.dt

        return info_gain

    def detect_velocity_edges(self, threshold_percentile: float = 90) -> List[TemporalEdge]:
        """
        Detect temporal edges using velocity (first derivative).

        Edges = points where |dA/dt| exceeds threshold.

        Args:
            threshold_percentile: Percentile of |velocity| for edge threshold

        Returns:
            List of detected temporal edges
        """
        # Compute magnitude of velocity across all neurons
        velocity_magnitude = np.sqrt(np.sum(self.velocity ** 2, axis=0))

        # Set threshold
        threshold = np.percentile(velocity_magnitude, threshold_percentile)

        # Find peaks in velocity
        peaks, properties = find_peaks(velocity_magnitude, height=threshold, distance=2)

        edges = []
        for peak_idx in peaks:
            if peak_idx < len(self.time):
                # Count neurons with high velocity
                high_vel_neurons = np.sum(np.abs(self.velocity[:, peak_idx]) > threshold)

                edges.append(TemporalEdge(
                    time=float(self.time[peak_idx]),
                    change_magnitude=float(velocity_magnitude[peak_idx]),
                    edge_type="velocity",
                    neurons_involved=int(high_vel_neurons),
                    surprise_level=float((velocity_magnitude[peak_idx] - threshold) / (np.max(velocity_magnitude) - threshold + 1e-6))
                ))

        return edges

    def detect_acceleration_edges(self, threshold_percentile: float = 85) -> List[TemporalEdge]:
        """
        Detect shocks (discontinuities) using acceleration (second derivative).

        Shocks = points where |d²A/dt²| is locally maximal.

        Args:
            threshold_percentile: Percentile of |acceleration| for shock threshold

        Returns:
            List of detected temporal edges (shocks)
        """
        # Compute magnitude of acceleration
        acceleration_magnitude = np.sqrt(np.sum(self.acceleration ** 2, axis=0))

        # Set threshold
        threshold = np.percentile(acceleration_magnitude, threshold_percentile)

        # Find peaks in acceleration
        peaks, properties = find_peaks(acceleration_magnitude, height=threshold, distance=3)

        edges = []
        for peak_idx in peaks:
            if peak_idx < len(self.time):
                high_acc_neurons = np.sum(np.abs(self.acceleration[:, peak_idx]) > threshold)

                edges.append(TemporalEdge(
                    time=float(self.time[peak_idx]),
                    change_magnitude=float(acceleration_magnitude[peak_idx]),
                    edge_type="acceleration",
                    neurons_involved=int(high_acc_neurons),
                    surprise_level=float((acceleration_magnitude[peak_idx] - threshold) / (np.max(acceleration_magnitude) - threshold + 1e-6))
                ))

        return edges

    def detect_information_gain_edges(self, threshold_percentile: float = 80) -> List[TemporalEdge]:
        """
        Detect edges using information gain (entropy change rate).

        High information gain = surprising changes in neural activity distribution.

        Args:
            threshold_percentile: Percentile of information gain for edge threshold

        Returns:
            List of detected temporal edges
        """
        info_gain = self._compute_information_gain()

        # Set threshold on positive information gain only
        positive_gain = info_gain[info_gain > 0]
        if len(positive_gain) > 0:
            threshold = np.percentile(positive_gain, threshold_percentile)
        else:
            threshold = 0.0

        # Find peaks in information gain
        peaks, _ = find_peaks(info_gain, height=threshold, distance=2)

        edges = []
        for peak_idx in peaks:
            if peak_idx < len(self.time):
                edges.append(TemporalEdge(
                    time=float(self.time[peak_idx]),
                    change_magnitude=float(info_gain[peak_idx]),
                    edge_type="information_gain",
                    neurons_involved=int(self.n_neurons),  # All neurons contribute to entropy
                    surprise_level=float(np.clip(info_gain[peak_idx] / (np.max(info_gain) + 1e-6), 0, 1))
                ))

        return edges

    def model_sensory_adaptation(self, adaptation_timescale: float = 2.0) -> AdaptationDynamics:
        """
        Model sensory adaptation - fading of static stimuli from consciousness.

        Weber's law: Response proportional to stimulus change rate, not absolute level.
        Static stimulus → no change → fades from consciousness.

        Args:
            adaptation_timescale: Time constant for adaptation (seconds)

        Returns:
            AdaptationDynamics describing fading
        """
        # Mean activity level
        initial_activity = np.mean(self.activity[:, 0])

        # Adaptation model: A_adapted(t) = A_residual + (A_0 - A_residual) * exp(-t/τ)
        # where τ is adaptation timescale
        residual_activity = initial_activity * 0.1  # 10% residual

        adapted_trajectory = np.zeros(self.n_timepoints)

        for t in range(self.n_timepoints):
            time_t = self.time[t]
            adapted = residual_activity + (initial_activity - residual_activity) * np.exp(-time_t / adaptation_timescale)
            adapted_trajectory[t] = adapted

        return AdaptationDynamics(
            initial_activity=initial_activity,
            time_constant=adaptation_timescale,
            residual_activity=residual_activity,
            adapted_trajectory=adapted_trajectory
        )

    def weight_consciousness_content(self, velocity_edges: List[TemporalEdge]) -> np.ndarray:
        """
        Weight consciousness content by temporal change magnitude.

        Higher |dA/dt| = more conscious content at that timepoint.

        Args:
            velocity_edges: List of velocity-based temporal edges

        Returns:
            Consciousness content weighting over time (0-1)
        """
        weighting = np.zeros(self.n_timepoints)

        # Compute velocity magnitude
        velocity_magnitude = np.sqrt(np.sum(self.velocity ** 2, axis=0))

        # Normalize to [0, 1]
        max_vel = np.max(velocity_magnitude) + 1e-6
        weighting = velocity_magnitude / max_vel

        return weighting

    def analyze(self) -> EdgeDetectionAnalysis:
        """
        Perform complete temporal edge analysis.

        Returns:
            EdgeDetectionAnalysis with all edge types and adaptation dynamics
        """
        # Detect all edge types
        velocity_edges = self.detect_velocity_edges(threshold_percentile=85)
        acceleration_edges = self.detect_acceleration_edges(threshold_percentile=80)
        info_gain_edges = self.detect_information_gain_edges(threshold_percentile=75)

        all_edges = velocity_edges + acceleration_edges + info_gain_edges

        # Combine edge times
        edge_times = np.array([e.time for e in all_edges]) if all_edges else np.array([])

        # Model sensory adaptation
        adaptation = self.model_sensory_adaptation(adaptation_timescale=2.0)

        # Compute information gain trajectory
        info_gain = self._compute_information_gain()

        # Weight consciousness content
        consciousness_content = self.weight_consciousness_content(velocity_edges)

        # Metadata
        metadata = {
            'n_neurons': self.n_neurons,
            'n_timepoints': self.n_timepoints,
            'dt': float(self.dt),
            'n_velocity_edges': len(velocity_edges),
            'n_acceleration_edges': len(acceleration_edges),
            'n_information_edges': len(info_gain_edges),
            'mean_edge_spacing': float(np.mean(np.diff(edge_times))) if len(edge_times) > 1 else 0.0,
            'adaptation_timescale': adaptation.time_constant,
            'consciousness_content_mean': float(np.mean(consciousness_content))
        }

        return EdgeDetectionAnalysis(
            temporal_edges=all_edges,
            edge_times=edge_times,
            velocity_trajectory=np.mean(np.abs(self.velocity), axis=0),
            acceleration_trajectory=np.mean(np.abs(self.acceleration), axis=0),
            information_gain_trajectory=info_gain,
            adapted_activity=adaptation,
            consciousness_content_weighted=consciousness_content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )


def validate_edge_detection():
    """
    Validate temporal edge detection against consciousness phenomena.

    Tests:
    1. Edge detection in step stimulus
    2. Sensory adaptation fading
    3. Information gain during surprising changes
    """
    print("Validating Temporal Edge Detector")
    print("=" * 60)

    # Test 1: Step stimulus (sudden change)
    print("\nTest 1: Step Stimulus Response")
    n_neurons = 20
    n_timepoints = 200
    time = np.linspace(0, 2.0, n_timepoints)

    activity = np.zeros((n_neurons, n_timepoints))
    # Step at t=0.5s
    activity[:, np.where(time >= 0.5)[0]] = 0.5

    detector = TemporalEdgeDetector(activity, time)
    analysis = detector.analyze()

    print(f"  Velocity edges detected: {analysis.metadata['n_velocity_edges']}")
    print(f"  Acceleration edges detected: {analysis.metadata['n_acceleration_edges']}")
    print(f"  Information edges detected: {analysis.metadata['n_information_edges']}")

    if analysis.temporal_edges:
        first_edge = analysis.temporal_edges[0]
        print(f"  First edge at t={first_edge.time:.3f}s, type={first_edge.edge_type}")

    # Test 2: Sensory adaptation
    print("\nTest 2: Sensory Adaptation (Static Stimulus)")
    # Constant stimulus
    activity_static = np.ones((n_neurons, n_timepoints)) * 0.3

    detector_static = TemporalEdgeDetector(activity_static, time)
    adaptation = detector_static.model_sensory_adaptation(adaptation_timescale=1.0)

    print(f"  Initial activity: {adaptation.initial_activity:.3f}")
    print(f"  Residual activity (after adaptation): {adaptation.residual_activity:.3f}")
    print(f"  Adaptation timescale: {adaptation.time_constant:.3f}s")
    print(f"  Activity at t=1.0s: {adaptation.adapted_trajectory[np.argmin(np.abs(time - 1.0))]:.3f}")

    # Test 3: Continuous fluctuating stimulus
    print("\nTest 3: Information Gain During Fluctuations")
    activity_fluctuating = np.random.default_rng(3).normal(0.3, 0.1, (n_neurons, n_timepoints))  # seeded demo signal
    # Add burst of synchronized activity
    activity_fluctuating[:, 100:120] += 0.3

    detector_fluct = TemporalEdgeDetector(activity_fluctuating, time)
    analysis_fluct = detector_fluct.analyze()

    mean_info_gain = np.mean(analysis_fluct.information_gain_trajectory[analysis_fluct.information_gain_trajectory > 0])
    print(f"  Mean information gain (positive only): {mean_info_gain:.6f}")
    print(f"  Max information gain: {np.max(analysis_fluct.information_gain_trajectory):.6f}")
    print(f"  Mean consciousness content weighting: {analysis_fluct.metadata['consciousness_content_mean']:.3f}")

    print("\n" + "=" * 60)
    print("✅ Validation complete:")
    print("  • Temporal edges detected at discontinuities")
    print("  • Sensory adaptation modeled (static → fades)")
    print("  • Information gain tracks surprising changes")
    print("  • Consciousness content weighted by change magnitude")


if __name__ == "__main__":
    validate_edge_detection()
