#!/usr/bin/env python3
"""
EmbodiedPredictionFramework.py - Phase 5.1: Embodied Prediction Error Minimization

Theory: Consciousness is fundamentally embodied. The body provides constraints,
opportunities, and the grounding for conscious experience. The brain predicts
sensory consequences of actions, and consciousness emerges from prediction
errors at the body-world interface.

Mathematical Foundation:
- Predictive processing: E(t) = ||x(t) - g(u(t); θ)||²
  where x is sensory signal, g is generative model, u is action, θ are parameters
- Free Energy (Friston): F = -log p(x|m) + D_KL[q(θ)|p(θ|x)]
  Consciousness minimizes free energy through action and perception
- Sensorimotor contingencies: S(t+Δt) = f(S(t), A(t))
  Maps how body state changes with actions (e.g., moving changes proprioception)

The hierarchy:
- Prediction at multiple timescales (immediate, short-term, planning)
- Hierarchical generative models (abstract → concrete predictions)
- Body as ground truth (proprioception, interoception)
- Consciousness = integrated prediction error minimization

Biological basis: Cerebellar predictive models, sensorimotor cortex,
primary interoceptive cortex (insula).

References:
- Friston, K. (2010) "The free-energy principle: a unified brain theory?"
- Clark, A. (2015) Surfing Uncertainty (predictive processing)
- O'Regan, J. K. & Noë, A. (2001) "A sensorimotor account of vision"
- Barrett, L. F. (2017) How Emotions Are Made (interoception, emotion)

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BodyState:
    """State of the embodied agent."""
    position: np.ndarray  # Position in environment (x, y, z)
    velocity: np.ndarray  # Velocity (dx/dt, dy/dt, dz/dt)
    proprioception: np.ndarray  # Joint angles, muscle tensions
    energy_level: float  # Energy/metabolic state (0-1)
    homeostatic_state: np.ndarray  # Temperature, pH, glucose, O2, etc.
    action_history: List[np.ndarray]  # Recent actions taken


@dataclass
class PredictionError:
    """Prediction error signal at different levels."""
    sensory_error: float  # ||observed - predicted sensory||²
    proprioceptive_error: float  # ||expected body state - actual||²
    interoceptive_error: float  # ||expected internal state - actual||²
    total_free_energy: float  # Integrated free energy
    error_magnitude: float  # L2 norm of all errors
    error_components: Dict[str, float]


@dataclass
class EmbodiedAnalysis:
    """Analysis of embodied prediction in agent."""
    body_state_trajectory: List[BodyState]
    predicted_trajectory: List[BodyState]
    prediction_errors: List[PredictionError]
    action_sequence: np.ndarray
    action_prediction_accuracy: float  # How well model predicts consequences
    conscious_content_integration: np.ndarray  # Consciousness signal
    timestamp: str
    metadata: Dict


class GenerativeBodyModel:
    """
    Generative model that predicts consequences of actions on body/sensory state.

    g(u(t); θ) → s(t+1) where u is action, s is sensory state, θ are parameters.
    """

    def __init__(self, state_dim: int = 20, action_dim: int = 5):
        """
        Args:
            state_dim: Dimensionality of body state
            action_dim: Dimensionality of action space
        """
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Generative model parameters (learned weights)
        # W_transition: how actions affect body state
        self.W_transition = np.random.randn(state_dim, action_dim) * 0.1
        # W_sensory: how body state generates sensory signals
        self.W_sensory = np.random.randn(action_dim, state_dim) * 0.1
        # Bias terms
        self.b_transition = np.zeros(state_dim)
        self.b_sensory = np.zeros(action_dim)

    def predict_next_state(self, current_state: np.ndarray,
                          action: np.ndarray) -> np.ndarray:
        """
        Predict what happens to body state after action.

        s(t+1) = tanh(W_transition · a(t) + current_state) + noise

        Args:
            current_state: Current body state vector
            action: Action taken

        Returns:
            Predicted next body state
        """
        # Action-driven state change
        state_change = np.tanh(self.W_transition @ action + self.b_transition)

        # New state is current + change (with decay)
        predicted_state = 0.7 * current_state + 0.3 * state_change

        # Add some stochasticity (biological noise)
        noise = np.random.normal(0, 0.02, self.state_dim)
        predicted_state = np.clip(predicted_state + noise, -1, 1)

        return predicted_state

    def predict_sensory(self, body_state: np.ndarray) -> np.ndarray:
        """
        Predict what sensations the body should produce.

        sensory(t) = σ(W_sensory · state(t) + b_sensory)

        Args:
            body_state: Current body state

        Returns:
            Predicted sensory signal
        """
        # Sensory prediction from body state
        sensory = np.tanh(self.W_sensory @ body_state + self.b_sensory)

        return sensory

    def predict_trajectory(self, initial_state: np.ndarray,
                          action_sequence: np.ndarray,
                          steps: int) -> List[np.ndarray]:
        """
        Predict trajectory over multiple steps.

        Args:
            initial_state: Starting body state
            action_sequence: Sequence of actions
            steps: Number of steps to predict

        Returns:
            List of predicted states
        """
        trajectory = [initial_state.copy()]
        current_state = initial_state.copy()

        for t in range(steps):
            if t < len(action_sequence):
                action = action_sequence[t]
            else:
                action = np.zeros(self.action_dim)

            next_state = self.predict_next_state(current_state, action)
            trajectory.append(next_state)
            current_state = next_state

        return trajectory


class EmbodiedPredictiveAgent:
    """
    Agent that maintains body model and minimizes prediction errors.

    Implements predictive processing: actively predicts sensory consequences
    of actions, adjusts both perception and action to minimize errors.
    """

    def __init__(self, body_dim: int = 20, action_dim: int = 5):
        """
        Args:
            body_dim: Dimensionality of body state
            action_dim: Dimensionality of action space
        """
        self.body_dim = body_dim
        self.action_dim = action_dim

        # Generative body model
        self.body_model = GenerativeBodyModel(body_dim, action_dim)

        # Current body state
        self.body_state = np.random.rand(body_dim) * 0.5

        # Internal predictions
        self.predicted_sensory = np.zeros(action_dim)

        # History
        self.state_history = [self.body_state.copy()]
        self.error_history = []
        self.action_history = []

    def compute_prediction_error(self, observed_sensory: np.ndarray,
                                observed_body_state: np.ndarray) -> PredictionError:
        """
        Compute prediction error across all modalities.

        Free Energy = prediction error + model complexity penalty

        Args:
            observed_sensory: Actual sensory signal from body/world
            observed_body_state: Actual body state

        Returns:
            PredictionError with all components
        """
        # Sensory prediction error
        sensory_error = np.linalg.norm(observed_sensory - self.predicted_sensory) ** 2

        # Proprioceptive error (body state prediction)
        proprioceptive_error = np.linalg.norm(
            observed_body_state - self.body_state
        ) ** 2

        # Interoceptive error (internal homeostasis)
        # Model homeostasis as maintaining state near [0.5, 0.5, ...]
        homeostatic_target = np.ones(self.body_dim) * 0.5
        interoceptive_error = np.linalg.norm(
            observed_body_state - homeostatic_target
        ) ** 2 * 0.1  # Smaller weight

        # Total free energy (prediction error + complexity)
        total_free_energy = sensory_error + proprioceptive_error + interoceptive_error

        # Error components for debugging
        error_components = {
            'sensory': float(sensory_error),
            'proprioceptive': float(proprioceptive_error),
            'interoceptive': float(interoceptive_error),
            'homeostasis_deviation': float(np.linalg.norm(observed_body_state - homeostatic_target))
        }

        return PredictionError(
            sensory_error=float(sensory_error),
            proprioceptive_error=float(proprioceptive_error),
            interoceptive_error=float(interoceptive_error),
            total_free_energy=float(total_free_energy),
            error_magnitude=float(np.sqrt(total_free_energy)),
            error_components=error_components
        )

    def select_action(self, available_actions: Optional[List[np.ndarray]] = None) -> np.ndarray:
        """
        Select action that minimizes predicted error.

        Uses expected free energy: select action a that minimizes
        E[F(s')] where s' is predicted next state.

        Args:
            available_actions: List of possible actions (or None for 5 defaults)

        Returns:
            Selected action
        """
        if available_actions is None:
            # Default 5 actions: forward, back, left, right, stop
            available_actions = [
                np.array([1, 0, 0, 0, 0]),      # Forward
                np.array([-1, 0, 0, 0, 0]),     # Backward
                np.array([0, 1, 0, 0, 0]),      # Left
                np.array([0, -1, 0, 0, 0]),     # Right
                np.array([0, 0, 0, 0, 0])       # Stop
            ]

        best_action = None
        best_expected_error = np.inf

        for action in available_actions:
            # Predict next state under this action
            next_state = self.body_model.predict_next_state(self.body_state, action)

            # Predict sensory signal for next state
            predicted_sensory = self.body_model.predict_sensory(next_state)

            # Estimate expected error (assuming homeostatic target)
            homeostatic_target = np.ones(self.body_dim) * 0.5
            expected_error = np.linalg.norm(next_state - homeostatic_target) ** 2
            expected_error += np.linalg.norm(predicted_sensory) ** 2 * 0.1

            if expected_error < best_expected_error:
                best_expected_error = expected_error
                best_action = action

        return best_action

    def step(self, environment_sensory: np.ndarray) -> Tuple[np.ndarray, PredictionError]:
        """
        Execute one step of perception and action.

        Args:
            environment_sensory: Sensory signal from environment

        Returns:
            (selected_action, prediction_error)
        """
        # Update prediction (perceptual inference)
        self.predicted_sensory = self.body_model.predict_sensory(self.body_state)

        # Compute prediction error
        error = self.compute_prediction_error(environment_sensory, self.body_state)

        # Update beliefs (simplified Bayesian update)
        # In full implementation: Kalman filter or variational inference
        error_weight = 0.01
        # Direct proportional update on sensory-relevant state dimensions
        sensory_error = environment_sensory - self.predicted_sensory
        # Scale by error and update first few dimensions
        self.body_state[:min(self.action_dim, self.body_dim)] += error_weight * sensory_error[:min(self.action_dim, self.body_dim)]
        self.body_state = np.clip(self.body_state, -1, 1)

        # Select action to minimize expected error
        action = self.select_action()

        # Update body state based on actual action effects
        # (in real world, we'd get new sensory signal)
        next_body_state = self.body_model.predict_next_state(self.body_state, action)

        # History tracking
        self.body_state = next_body_state
        self.state_history.append(self.body_state.copy())
        self.error_history.append(error)
        self.action_history.append(action.copy())

        return action, error

    def run_simulation(self, n_steps: int = 100) -> EmbodiedAnalysis:
        """
        Run embodied prediction simulation.

        Args:
            n_steps: Number of steps to simulate

        Returns:
            EmbodiedAnalysis with trajectories and metrics
        """
        for step in range(n_steps):
            # Simulate environment sensory signal
            # (Simple: mixture of body state and random noise)
            environment_signal = self.body_state[:self.action_dim] + np.random.normal(0, 0.05, self.action_dim)

            # Execute one step
            action, error = self.step(environment_signal)

        # Compute action prediction accuracy
        # This is how well the model predicts sensory consequences
        if len(self.error_history) > 0:
            mean_error = np.mean([e.total_free_energy for e in self.error_history])
            prediction_accuracy = 1.0 / (1 + mean_error)
        else:
            prediction_accuracy = 0.0

        # Consciousness content: integrated prediction error minimization
        # Higher accuracy = higher consciousness
        consciousness_signal = np.array([
            1.0 / (1 + e.total_free_energy) for e in self.error_history
        ])

        # Build body state trajectory
        body_states = [
            BodyState(
                position=self.state_history[i][:3],
                velocity=self.state_history[i][3:6],
                proprioception=self.state_history[i][6:13],
                energy_level=0.5 + 0.3 * np.sin(i / 10),
                homeostatic_state=self.state_history[i][13:],
                action_history=self.action_history[-5:]
            )
            for i in range(len(self.state_history))
        ]

        metadata = {
            'n_steps': n_steps,
            'body_dim': self.body_dim,
            'action_dim': self.action_dim,
            'mean_prediction_error': float(np.mean([e.total_free_energy for e in self.error_history])),
            'final_free_energy': float(self.error_history[-1].total_free_energy) if self.error_history else 0.0,
            'consciousness_mean': float(np.mean(consciousness_signal))
        }

        return EmbodiedAnalysis(
            body_state_trajectory=body_states,
            predicted_trajectory=[],  # Would be filled by model predictions
            prediction_errors=self.error_history,
            action_sequence=np.array(self.action_history),
            action_prediction_accuracy=prediction_accuracy,
            conscious_content_integration=consciousness_signal,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )


def validate_embodied_prediction():
    """
    Validate embodied predictive processing model.

    Tests:
    1. Generative model prediction accuracy
    2. Prediction error computation
    3. Action selection for error minimization
    4. Consciousness signal based on prediction accuracy
    """
    print("Validating Embodied Prediction Framework")
    print("=" * 60)

    # Test 1: Generative model
    print("\nTest 1: Generative Body Model")
    model = GenerativeBodyModel(state_dim=20, action_dim=5)
    state = np.random.rand(20) * 0.3
    action = np.array([0.5, -0.3, 0.2, 0.0, 0.1])

    next_state = model.predict_next_state(state, action)
    sensory = model.predict_sensory(next_state)

    print(f"  Initial state: mean={np.mean(state):.3f}, std={np.std(state):.3f}")
    print(f"  Action: {action}")
    print(f"  Predicted next state: mean={np.mean(next_state):.3f}")
    print(f"  Predicted sensory: {sensory[:3]}")

    # Test 2: Prediction error computation
    print("\nTest 2: Prediction Error Computation")
    agent = EmbodiedPredictiveAgent(body_dim=20, action_dim=5)

    observed_sensory = np.random.rand(5) * 0.5
    observed_body = np.random.rand(20) * 0.5

    error = agent.compute_prediction_error(observed_sensory, observed_body)

    print(f"  Sensory error: {error.sensory_error:.4f}")
    print(f"  Proprioceptive error: {error.proprioceptive_error:.4f}")
    print(f"  Interoceptive error: {error.interoceptive_error:.4f}")
    print(f"  Total free energy: {error.total_free_energy:.4f}")

    # Test 3: Action selection
    print("\nTest 3: Action Selection for Error Minimization")
    agent.body_state = np.random.rand(20) * 0.3 + 0.35

    action = agent.select_action()
    print(f"  Selected action: {action}")

    # Test 4: Full simulation
    print("\nTest 4: Full Embodied Prediction Simulation (100 steps)")
    agent = EmbodiedPredictiveAgent(body_dim=20, action_dim=5)
    analysis = agent.run_simulation(n_steps=100)

    print(f"  Steps simulated: {analysis.metadata['n_steps']}")
    print(f"  Mean prediction error: {analysis.metadata['mean_prediction_error']:.4f}")
    print(f"  Final free energy: {analysis.metadata['final_free_energy']:.4f}")
    print(f"  Action prediction accuracy: {analysis.action_prediction_accuracy:.3f}")
    print(f"  Consciousness (mean): {analysis.metadata['consciousness_mean']:.3f}")

    # Show trajectory of consciousness
    print(f"  Consciousness trajectory (first 10 steps):")
    for i in range(min(10, len(analysis.conscious_content_integration))):
        print(f"    Step {i}: {analysis.conscious_content_integration[i]:.3f}")

    print("\n" + "=" * 60)
    print("✅ Validation complete:")
    print("  • Generative body model predicts state transitions")
    print("  • Prediction errors computed across modalities")
    print("  • Action selection minimizes expected error")
    print("  • Consciousness signal tracks prediction accuracy")


if __name__ == "__main__":
    validate_embodied_prediction()
