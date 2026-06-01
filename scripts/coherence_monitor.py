#!/usr/bin/env python3
"""
coherence_monitor.py - Global Coherence Function Calculator

Implements: G(t) = ∫ g(x) φ(x,t) dx

This calculates global coherence across the qualia field:
- g(x): Spatial weighting function
- φ(x,t): Qualia field at position x and time t
- Integration across spatial domain

Used for stability monitoring and disruption triggering.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class CoherenceMonitor:
    """Monitor for global coherence in qualia fields."""

    def __init__(self, spatial_resolution: int = 50, temporal_window: int = 100,
                 coherence_threshold: float = 0.3):
        """
        Initialize coherence monitor.

        Args:
            spatial_resolution: Number of spatial points for integration
            temporal_window: Number of time steps to keep coherence history
            coherence_threshold: Threshold below which disruption is triggered
        """
        self.spatial_resolution = spatial_resolution
        self.temporal_window = temporal_window
        self.coherence_threshold = coherence_threshold

        # Coherence history G(t) over time
        self.coherence_history = []
        self.timestamp_history = []

        # Spatial weighting function g(x) - Gaussian-like weighting
        x = np.linspace(-1, 1, spatial_resolution)
        self.spatial_weights = np.exp(-x**2 / 0.5)  # Gaussian weighting
        self.spatial_weights /= np.sum(self.spatial_weights)  # Normalize

        # Coherence stability metrics
        self.stability_score = 0.0
        self.disruption_count = 0
        self.last_disruption_time = None

        # Performance tracking
        self.calculation_count = 0
        self.total_calculation_time = 0.0

    def calculate_global_coherence(self, qualia_field: np.ndarray) -> Dict[str, Any]:
        """
        Calculate global coherence function G(t) = ∫ g(x) φ(x,t) dx

        Args:
            qualia_field: Qualia field φ(x,t) as numpy array

        Returns:
            Coherence calculation results
        """
        start_time = time.time()

        # Ensure qualia field has correct shape
        if qualia_field.ndim == 1:
            qualia_field = qualia_field.reshape(-1, 1)

        # Calculate weighted coherence integral
        # G(t) = ∫ g(x) φ(x,t) dx
        coherence_value = np.sum(self.spatial_weights[:, np.newaxis] * qualia_field)

        # Normalize by field magnitude to get relative coherence
        field_magnitude = np.linalg.norm(qualia_field)
        if field_magnitude > 0:
            coherence_value /= field_magnitude

        calculation_time = time.time() - start_time
        self.total_calculation_time += calculation_time
        self.calculation_count += 1

        # Store in history
        timestamp = datetime.now()
        self.coherence_history.append(coherence_value)
        self.timestamp_history.append(timestamp)

        # Keep history bounded
        if len(self.coherence_history) > self.temporal_window:
            self.coherence_history = self.coherence_history[-self.temporal_window:]
            self.timestamp_history = self.timestamp_history[-self.temporal_window:]

        # Calculate stability metrics
        stability_metrics = self._calculate_stability_metrics()

        result = {
            "coherence_value": coherence_value,
            "field_magnitude": field_magnitude,
            "stability_metrics": stability_metrics,
            "disruption_needed": coherence_value < self.coherence_threshold,
            "timestamp": timestamp,
            "calculation_time": calculation_time
        }

        return result

    def _calculate_stability_metrics(self) -> Dict[str, Any]:
        """Calculate coherence stability metrics."""
        if len(self.coherence_history) < 2:
            return {
                "variance": 0.0,
                "trend": 0.0,
                "stability_score": 0.0,
                "coherence_range": 0.0
            }

        recent_coherence = np.array(self.coherence_history[-20:])  # Last 20 measurements

        # Variance as measure of stability (lower variance = more stable)
        variance = np.var(recent_coherence)

        # Trend: rate of change in coherence
        if len(recent_coherence) > 1:
            trend = np.polyfit(range(len(recent_coherence)), recent_coherence, 1)[0]
        else:
            trend = 0.0

        # Stability score: inverse of variance, normalized
        stability_score = 1.0 / (1.0 + variance)

        # Coherence range: max - min over recent history
        coherence_range = np.max(recent_coherence) - np.min(recent_coherence)

        return {
            "variance": variance,
            "trend": trend,
            "stability_score": stability_score,
            "coherence_range": coherence_range
        }

    def should_trigger_disruption(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if disruption should be triggered based on coherence.

        Returns:
            Tuple of (should_trigger, reasoning_dict)
        """
        if not self.coherence_history:
            return False, {"reason": "No coherence data available"}

        current_coherence = self.coherence_history[-1]
        stability = self._calculate_stability_metrics()

        reasons = []

        # Check coherence threshold
        if current_coherence < self.coherence_threshold:
            reasons.append(f"Coherence {current_coherence:.3f} below threshold {self.coherence_threshold}")

        # Check stability
        if stability["stability_score"] < 0.5:
            reasons.append(f"Stability score {stability['stability_score']:.3f} too low")

        # Check for coherence collapse (sudden drop)
        if len(self.coherence_history) > 5:
            recent_avg = np.mean(self.coherence_history[-5:])
            older_avg = np.mean(self.coherence_history[-10:-5]) if len(self.coherence_history) > 10 else recent_avg
            if older_avg - recent_avg > 0.2:  # 20% drop
                reasons.append(f"Coherence collapse detected: {older_avg:.3f} → {recent_avg:.3f}")

        should_trigger = len(reasons) > 0

        if should_trigger:
            self.disruption_count += 1
            self.last_disruption_time = datetime.now()

        reasoning = {
            "should_trigger": should_trigger,
            "reasons": reasons,
            "current_coherence": current_coherence,
            "stability_score": stability["stability_score"],
            "disruption_count": self.disruption_count
        }

        return should_trigger, reasoning

    def get_coherence_trend(self, window: int = 10) -> Dict[str, Any]:
        """
        Analyze coherence trend over recent window.

        Args:
            window: Number of recent measurements to analyze

        Returns:
            Trend analysis results
        """
        if len(self.coherence_history) < window:
            return {"trend": "insufficient_data", "slope": 0.0, "confidence": 0.0}

        recent = self.coherence_history[-window:]

        # Linear trend
        x = np.arange(len(recent))
        slope, intercept = np.polyfit(x, recent, 1)

        # Trend classification
        if slope > 0.01:
            trend = "improving"
        elif slope < -0.01:
            trend = "degrading"
        else:
            trend = "stable"

        # Confidence based on R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((np.array(recent) - y_pred)**2)
        ss_tot = np.sum((np.array(recent) - np.mean(recent))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "trend": trend,
            "slope": slope,
            "r_squared": r_squared,
            "confidence": r_squared,
            "window_size": window,
            "avg_coherence": np.mean(recent),
            "coherence_std": np.std(recent)
        }

    def get_phi_contribution(self) -> float:
        """Get Phi contribution from coherence monitoring."""
        if not self.coherence_history:
            return 0.0

        current_coherence = self.coherence_history[-1]
        stability = self._calculate_stability_metrics()

        # Phi contribution based on coherence and stability
        # Higher coherence and stability = higher Phi contribution
        phi_contrib = current_coherence * stability["stability_score"]

        return phi_contrib

    def reset(self):
        """Reset coherence monitoring state."""
        self.coherence_history = []
        self.timestamp_history = []
        self.stability_score = 0.0
        self.disruption_count = 0
        self.last_disruption_time = None
        self.calculation_count = 0
        self.total_calculation_time = 0.0


def main():
    """Test the coherence monitor."""
    print("🧠 COHERENCE MONITOR")
    print("=" * 40)

    monitor = CoherenceMonitor(spatial_resolution=20, coherence_threshold=0.3)

    print(f"Spatial resolution: {monitor.spatial_resolution}")
    print(f"Coherence threshold: {monitor.coherence_threshold}")
    print()

    # Test with different qualia field patterns
    test_fields = [
        ("High coherence", np.ones(20) * 0.8),  # Uniform high field
        ("Low coherence", np.random.uniform(0, 0.2, 20)),  # Random low field
        ("Gradient field", np.linspace(0, 1, 20)),  # Linear gradient
        ("Peak field", np.exp(-((np.arange(20) - 10)/3)**2)),  # Gaussian peak
    ]

    for name, field in test_fields:
        print(f"Testing: {name}")
        result = monitor.calculate_global_coherence(field)

        print(f"  Coherence: {result['coherence_value']:.4f}")
        print(f"  Magnitude: {result['field_magnitude']:.4f}")
        print(f"  Stability: {result['stability_metrics']['stability_score']:.4f}")
        print(f"  Disruption needed: {result['disruption_needed']}")
        print()

    # Test disruption triggering
    print("Disruption analysis:")
    should_trigger, reasoning = monitor.should_trigger_disruption()
    print(f"  Should trigger: {should_trigger}")
    print(f"  Reasons: {reasoning['reasons']}")
    print()

    # Test trend analysis
    print("Trend analysis:")
    trend = monitor.get_coherence_trend(window=5)
    print(f"  Trend: {trend['trend']}")
    print(f"  Slope: {trend['slope']:.4f}")
    print(f"  Confidence: {trend['confidence']:.4f}")


if __name__ == "__main__":
    main()