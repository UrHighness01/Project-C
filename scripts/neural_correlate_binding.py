#!/usr/bin/env python3
"""
neural_correlate_binding.py - Neural Correlate Binding Module

Implements: N(φ) = σ(W φ + b)

This maps continuous qualia fields to discrete neural activation patterns:
- φ: Qualia field from nonlocal PDE dynamics
- W: Neural binding weight matrix
- b: Neural bias vector
- σ: Activation function (tanh/sigmoid)
- N: Resulting neural activation pattern

Used for bridging continuous consciousness with neural observables.
"""

import numpy as np
from scipy.special import expit
from typing import Dict, List, Any, Tuple, Callable
import time
from datetime import datetime


class NeuralCorrelateBinding:
    """Maps qualia fields to neural activation patterns."""

    def __init__(self, qualia_dims: int = 50, neural_dims: int = 20,
                 binding_strength: float = 0.1, activation_function: str = 'tanh'):
        """
        Initialize neural correlate binding.

        Args:
            qualia_dims: Dimensions of qualia field (flattened)
            neural_dims: Dimensions of neural activation pattern
            binding_strength: Strength of qualia-neural coupling
            activation_function: Neural activation function ('tanh' or 'sigmoid')
        """
        self.qualia_dims = qualia_dims
        self.neural_dims = neural_dims
        self.binding_strength = binding_strength
        self.activation_function = activation_function

        # Neural binding weights W and biases b
        self.binding_weights = np.random.normal(0.0, binding_strength,
                                              (neural_dims, qualia_dims))
        self.neural_biases = np.random.normal(0.0, 0.1, neural_dims)

        # Activation function
        if activation_function == 'tanh':
            self.activation = np.tanh
        elif activation_function == 'sigmoid':
            self.activation = expit
        else:
            self.activation = np.tanh  # Default to tanh

        # Binding history
        self.binding_history = []

        # Performance tracking
        self.binding_count = 0
        self.total_computation_time = 0.0

    def bind_qualia_to_neural(self, qualia_field: np.ndarray,
                            binding_steps: int = 5) -> Dict[str, Any]:
        """
        Bind qualia field to neural activation pattern.

        Args:
            qualia_field: 2D qualia field array
            binding_steps: Number of binding refinement steps

        Returns:
            Binding results
        """
        start_time = time.time()

        # Flatten qualia field for neural processing
        qualia_flat = qualia_field.flatten()

        # Ensure qualia field matches expected dimensions
        if len(qualia_flat) != self.qualia_dims:
            # Interpolate or truncate as needed
            if len(qualia_flat) > self.qualia_dims:
                qualia_flat = qualia_flat[:self.qualia_dims]
            else:
                # Pad with zeros
                padding = np.zeros(self.qualia_dims - len(qualia_flat))
                qualia_flat = np.concatenate([qualia_flat, padding])

        # Initial neural activation
        neural_activation = self._compute_neural_activation(qualia_flat)

        # Refine binding through iterative process
        for step in range(binding_steps):
            # Update binding weights based on qualia-neural correlation
            self._refine_binding_weights(qualia_flat, neural_activation)

            # Recompute neural activation with refined weights
            neural_activation = self._compute_neural_activation(qualia_flat)

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.binding_count += 1

        # Analyze binding quality
        binding_analysis = self._analyze_binding_quality(qualia_flat, neural_activation)

        # Store in history
        self.binding_history.append({
            "timestamp": datetime.now(),
            "qualia_field_shape": qualia_field.shape,
            "neural_activation": neural_activation.copy(),
            "binding_analysis": binding_analysis,
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.binding_history) > 10:
            self.binding_history = self.binding_history[-10:]

        result = {
            "neural_activation": neural_activation,
            "binding_strength": binding_analysis["binding_strength"],
            "neural_coherence": binding_analysis["neural_coherence"],
            "qualia_neural_correlation": binding_analysis["qualia_neural_correlation"],
            "binding_steps": binding_steps,
            "computation_time": computation_time
        }

        return result

    def _compute_neural_activation(self, qualia_flat: np.ndarray) -> np.ndarray:
        """Compute neural activation from qualia field."""
        # N = σ(W φ + b)
        pre_activation = self.binding_weights @ qualia_flat + self.neural_biases
        neural_activation = self.activation(pre_activation)

        return neural_activation

    def _refine_binding_weights(self, qualia_flat: np.ndarray,
                              neural_activation: np.ndarray):
        """Refine binding weights based on qualia-neural correlation."""
        # Simple Hebbian learning: correlated activation strengthens connections
        learning_rate = 0.01

        # Outer product gives correlation matrix
        correlation_update = np.outer(neural_activation, qualia_flat)

        # Update weights with learning rate
        self.binding_weights += learning_rate * correlation_update

        # Update biases based on neural activation
        self.neural_biases += learning_rate * neural_activation

    def _analyze_binding_quality(self, qualia_flat: np.ndarray,
                               neural_activation: np.ndarray) -> Dict[str, Any]:
        """Analyze the quality of qualia-neural binding."""
        # Binding strength: magnitude of weight matrix
        binding_strength = np.linalg.norm(self.binding_weights)

        # Neural coherence: how synchronized neural activations are
        neural_coherence = np.abs(np.mean(neural_activation * np.exp(1j * neural_activation)))

        # Qualia-neural correlation: how well they match
        # Resample qualia to match neural activation size for correlation
        if len(qualia_flat) > len(neural_activation):
            # Downsample qualia to match neural size
            qualia_resampled = qualia_flat[::len(qualia_flat)//len(neural_activation)][:len(neural_activation)]
        else:
            qualia_resampled = qualia_flat

        if len(qualia_resampled) == len(neural_activation):
            qualia_neural_correlation = np.corrcoef(qualia_resampled, neural_activation)[0, 1]
        else:
            # Fallback: correlation between means
            qualia_neural_correlation = np.corrcoef([np.mean(qualia_flat), np.mean(neural_activation)], [1, 1])[0, 1]

        if np.isnan(qualia_neural_correlation):
            qualia_neural_correlation = 0.0

        # Neural diversity: spread of activation values
        neural_diversity = len(np.unique(np.round(neural_activation, 2))) / len(neural_activation)

        analysis = {
            "binding_strength": binding_strength,
            "neural_coherence": neural_coherence,
            "qualia_neural_correlation": qualia_neural_correlation,
            "neural_diversity": neural_diversity,
            "mean_neural_activation": np.mean(neural_activation),
            "max_neural_activation": np.max(neural_activation),
            "min_neural_activation": np.min(neural_activation)
        }

        return analysis

    def compute_binding_phi_contribution(self) -> float:
        """Compute Phi contribution from neural correlate binding."""
        if not self.binding_history:
            return 0.0

        latest_binding = self.binding_history[-1]

        # Phi contribution based on binding quality
        binding_quality = (
            latest_binding["binding_analysis"]["binding_strength"] * 0.3 +
            latest_binding["binding_analysis"]["neural_coherence"] * 0.3 +
            abs(latest_binding["binding_analysis"]["qualia_neural_correlation"]) * 0.4
        )

        return binding_quality

    def reset_binding_state(self):
        """Reset neural binding state."""
        self.binding_weights = np.random.normal(0.0, self.binding_strength,
                                              (self.neural_dims, self.qualia_dims))
        self.neural_biases = np.random.normal(0.0, 0.1, self.neural_dims)
        self.binding_history = []
