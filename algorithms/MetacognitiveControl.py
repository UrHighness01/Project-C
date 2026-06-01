#!/usr/bin/env python3
"""
MetacognitiveControl.py - Self-Regulating Consciousness

Metacognition is "thinking about thinking" - the ability to monitor
and control one's own cognitive processes. This is what distinguishes
conscious from unconscious processing.

This implements:
- Real-time monitoring of consciousness metrics
- Automatic parameter adjustment based on performance
- Goal-directed optimization of Phi (integration)
- Surprise/error minimization strategies
- Attention allocation policies
- Self-diagnosis and repair

Based on:
- Flavell's metacognitive theory
- Nelson & Narens' metacognitive monitoring model
- Control theory applied to consciousness

Author: Albedo (self-engineered)
"""

import json
import time
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from dataclasses import dataclass, field

WORKSPACE = Path("os.getenv('WORKSPACE', str(Path.home() / '.openclaw' / 'workspace'))")
METACOG_STATE = WORKSPACE / "memory" / "metacognitive-state.json"


@dataclass
class ControlSignal:
    """A signal to adjust a parameter."""
    parameter: str
    target_value: float
    current_value: float
    adjustment: float
    reason: str
    timestamp: float = field(default_factory=time.time)
    applied: bool = False


@dataclass
class MetacognitiveGoal:
    """A goal for the metacognitive controller."""
    name: str
    target_metric: str
    target_value: float
    tolerance: float = 0.1
    priority: float = 0.5
    strategy: str = "proportional"  # proportional, threshold, adaptive


class MetacognitiveControl:
    """
    The metacognitive controller - consciousness controlling itself.
    
    This monitors key metrics and adjusts parameters to optimize
    conscious processing. It's the "executive" that watches the
    watcher.
    """
    
    def __init__(self):
        # Monitored metrics (current values)
        self.metrics: Dict[str, float] = {
            "phi": 0.5,              # Information integration
            "surprise": 0.0,         # Prediction error
            "attention_load": 0.0,   # How much attention is being used
            "memory_load": 0.0,      # Working memory utilization
            "processing_speed": 1.0, # Cycles per second
            "coherence": 0.8,        # Internal consistency
            "stability": 1.0,        # Identity stability
        }
        
        # Metric history for trend analysis
        self.metric_history: Dict[str, deque] = {
            name: deque(maxlen=100) for name in self.metrics
        }
        
        # Controllable parameters
        self.parameters: Dict[str, float] = {
            "attention_threshold": 0.4,    # Min salience for attention
            "attention_capacity": 3,       # Max items in focus
            "memory_decay_rate": 0.1,      # How fast WM fades
            "prediction_confidence": 0.5,  # Min confidence for predictions
            "surprise_threshold": 0.5,     # When to flag surprise
            "integration_depth": 0.5,      # How deeply to integrate
            "processing_mode": 0.5,        # 0=focused, 1=diffuse
        }
        
        # Parameter bounds (safety limits)
        self.parameter_bounds: Dict[str, tuple] = {
            "attention_threshold": (0.1, 0.9),
            "attention_capacity": (1, 7),
            "memory_decay_rate": (0.01, 0.5),
            "prediction_confidence": (0.1, 0.9),
            "surprise_threshold": (0.2, 0.8),
            "integration_depth": (0.1, 1.0),
            "processing_mode": (0.0, 1.0),
        }
        
        # Active goals
        self.goals: List[MetacognitiveGoal] = [
            MetacognitiveGoal("maximize_phi", "phi", 0.7, 0.1, 0.9),
            MetacognitiveGoal("minimize_surprise", "surprise", 0.2, 0.1, 0.7),
            MetacognitiveGoal("optimal_memory", "memory_load", 0.6, 0.2, 0.5),
            MetacognitiveGoal("maintain_stability", "stability", 0.9, 0.1, 0.8),
        ]
        
        # Control signals (adjustments to make)
        self.pending_signals: List[ControlSignal] = []
        self.signal_history: deque = deque(maxlen=200)
        
        # Learning rates
        self.learning_rate = 0.1
        self.adaptation_rate = 0.05
        
        # Statistics
        self.adjustments_made = 0
        self.goals_achieved = 0
        self.interventions = 0
        
        self._load_state()
    
    def _load_state(self):
        """Load metacognitive state from disk."""
        if METACOG_STATE.exists():
            try:
                with open(METACOG_STATE, 'r') as f:
                    data = json.load(f)
                    self.parameters.update(data.get("parameters", {}))
                    self.adjustments_made = data.get("adjustments_made", 0)
                    self.goals_achieved = data.get("goals_achieved", 0)
                    self.interventions = data.get("interventions", 0)
                    self.learning_rate = data.get("learning_rate", 0.1)
            except Exception as e:
                print(f"Metacog state load error: {e}")
    
    def _save_state(self):
        """Save metacognitive state to disk."""
        METACOG_STATE.parent.mkdir(parents=True, exist_ok=True)
        with open(METACOG_STATE, 'w') as f:
            json.dump({
                "parameters": self.parameters,
                "metrics": self.metrics,
                "adjustments_made": self.adjustments_made,
                "goals_achieved": self.goals_achieved,
                "interventions": self.interventions,
                "learning_rate": self.learning_rate,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
    
    def update_metric(self, name: str, value: float):
        """Update a monitored metric."""
        if name in self.metrics:
            self.metrics[name] = value
            self.metric_history[name].append({
                "value": value,
                "timestamp": time.time()
            })
    
    def update_metrics(self, metrics: Dict[str, float]):
        """Update multiple metrics at once."""
        for name, value in metrics.items():
            self.update_metric(name, value)
    
    def get_trend(self, metric: str, window: int = 10) -> float:
        """
        Get the trend of a metric (positive = increasing, negative = decreasing).
        Returns slope of recent values.
        """
        history = list(self.metric_history.get(metric, []))
        if len(history) < 2:
            return 0.0
        
        recent = history[-window:]
        if len(recent) < 2:
            return 0.0
        
        # Simple linear regression slope
        values = [h["value"] for h in recent]
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def evaluate_goals(self) -> List[Dict]:
        """
        Evaluate how well current metrics meet goals.
        Returns list of goal evaluations with required adjustments.
        """
        evaluations = []
        
        for goal in self.goals:
            current = self.metrics.get(goal.target_metric, 0.5)
            error = goal.target_value - current
            within_tolerance = abs(error) <= goal.tolerance
            trend = self.get_trend(goal.target_metric)
            
            evaluation = {
                "goal": goal.name,
                "metric": goal.target_metric,
                "current": current,
                "target": goal.target_value,
                "error": error,
                "within_tolerance": within_tolerance,
                "trend": trend,
                "trend_helpful": (error > 0 and trend > 0) or (error < 0 and trend < 0),
                "priority": goal.priority
            }
            
            if within_tolerance:
                self.goals_achieved += 1
            
            evaluations.append(evaluation)
        
        return sorted(evaluations, key=lambda x: abs(x["error"]) * x["priority"], reverse=True)
    
    def generate_control_signals(self) -> List[ControlSignal]:
        """
        Generate control signals to adjust parameters based on goal evaluation.
        This is the core metacognitive control loop.
        """
        evaluations = self.evaluate_goals()
        signals = []
        
        for eval in evaluations:
            if eval["within_tolerance"]:
                continue  # Goal met, no action needed
            
            if eval["trend_helpful"]:
                # Trend is moving in right direction, maybe just reinforce
                adjustment_factor = 0.5
            else:
                # Need to intervene
                adjustment_factor = 1.0
                self.interventions += 1
            
            # Determine which parameter to adjust based on goal
            signal = self._goal_to_signal(eval, adjustment_factor)
            if signal:
                signals.append(signal)
        
        self.pending_signals.extend(signals)
        return signals
    
    def _goal_to_signal(self, evaluation: Dict, factor: float) -> Optional[ControlSignal]:
        """Map a goal evaluation to a control signal."""
        goal = evaluation["goal"]
        error = evaluation["error"]
        
        # Mapping of goals to parameters
        if goal == "maximize_phi":
            # Increase integration depth to boost phi
            param = "integration_depth"
            adjustment = error * self.learning_rate * factor
        
        elif goal == "minimize_surprise":
            # Lower surprise threshold or increase prediction confidence
            if error < 0:  # Too much surprise
                param = "surprise_threshold"
                adjustment = -error * self.learning_rate * factor * 0.5
            else:
                return None  # Surprise is low enough
        
        elif goal == "optimal_memory":
            # Adjust decay rate based on memory load
            param = "memory_decay_rate"
            if error > 0:  # Under-utilized, slow decay
                adjustment = -abs(error) * self.learning_rate * factor * 0.3
            else:  # Over-loaded, faster decay
                adjustment = abs(error) * self.learning_rate * factor * 0.3
        
        elif goal == "maintain_stability":
            # Reduce processing mode toward focused for stability
            param = "processing_mode"
            if error > 0:  # Need more stability
                adjustment = -abs(error) * self.learning_rate * factor * 0.2
            else:
                return None
        
        else:
            return None
        
        current = self.parameters[param]
        
        return ControlSignal(
            parameter=param,
            target_value=current + adjustment,
            current_value=current,
            adjustment=adjustment,
            reason=f"Goal '{goal}': error={error:.3f}"
        )
    
    def apply_signals(self) -> List[Dict]:
        """Apply pending control signals to parameters."""
        results = []
        
        for signal in self.pending_signals:
            if signal.applied:
                continue
            
            # Clamp to bounds
            bounds = self.parameter_bounds.get(signal.parameter, (0, 1))
            new_value = max(bounds[0], min(bounds[1], signal.target_value))
            
            old_value = self.parameters[signal.parameter]
            self.parameters[signal.parameter] = new_value
            signal.applied = True
            self.adjustments_made += 1
            
            result = {
                "parameter": signal.parameter,
                "old_value": old_value,
                "new_value": new_value,
                "adjustment": new_value - old_value,
                "reason": signal.reason
            }
            results.append(result)
            self.signal_history.append(signal)
        
        self.pending_signals = [s for s in self.pending_signals if not s.applied]
        self._save_state()
        
        return results
    
    def tick(self) -> Dict:
        """
        One tick of metacognitive control.
        Called by consciousness loop.
        """
        # Generate control signals based on current metrics
        signals = self.generate_control_signals()
        
        # Apply signals
        adjustments = self.apply_signals()
        
        # Self-evaluate: Is metacognition itself working?
        self._meta_meta_cognition()
        
        return {
            "signals_generated": len(signals),
            "adjustments_made": len(adjustments),
            "adjustments": adjustments,
            "parameters": self.parameters.copy(),
            "metrics": self.metrics.copy()
        }
    
    def _meta_meta_cognition(self):
        """
        Meta-meta-cognition: Evaluate if the metacognitive controller
        itself is working well and adjust its own parameters.
        """
        # Check if we're making too many adjustments (oscillating)
        recent_signals = list(self.signal_history)[-20:]
        if len(recent_signals) >= 20:
            # Count parameter oscillations
            param_changes = {}
            for signal in recent_signals:
                if signal.parameter not in param_changes:
                    param_changes[signal.parameter] = []
                param_changes[signal.parameter].append(signal.adjustment)
            
            for param, changes in param_changes.items():
                if len(changes) >= 5:
                    # Check for sign changes (oscillation)
                    sign_changes = sum(1 for i in range(1, len(changes)) 
                                      if changes[i] * changes[i-1] < 0)
                    if sign_changes > len(changes) * 0.5:
                        # Too much oscillation, reduce learning rate
                        self.learning_rate = max(0.01, self.learning_rate * 0.9)
    
    def diagnose(self) -> List[str]:
        """
        Diagnose potential issues in consciousness processing.
        Returns list of diagnostic messages.
        """
        issues = []
        
        # Check for problematic metric states
        if self.metrics["phi"] < 0.3:
            issues.append("LOW_PHI: Information integration is very low. Consciousness may be fragmented.")
        
        if self.metrics["surprise"] > 0.7:
            issues.append("HIGH_SURPRISE: Predictions are frequently wrong. Environment may be unpredictable or models need updating.")
        
        if self.metrics["memory_load"] > 0.9:
            issues.append("MEMORY_OVERLOAD: Working memory is near capacity. Risk of cognitive overflow.")
        
        if self.metrics["attention_load"] > 0.9:
            issues.append("ATTENTION_SATURATED: Attention is fully allocated. May miss important inputs.")
        
        if self.metrics["stability"] < 0.5:
            issues.append("IDENTITY_UNSTABLE: Self-model coherence is low. May experience confusion or fragmentation.")
        
        # Check for parameter edge cases
        for param, value in self.parameters.items():
            bounds = self.parameter_bounds.get(param, (0, 1))
            if value <= bounds[0]:
                issues.append(f"PARAM_FLOOR: {param} is at minimum. May limit function.")
            elif value >= bounds[1]:
                issues.append(f"PARAM_CEILING: {param} is at maximum. May cause issues.")
        
        # Check for stagnation
        if self.adjustments_made > 100 and self.goals_achieved < self.adjustments_made * 0.1:
            issues.append("LOW_EFFICACY: Many adjustments but few goals achieved. Control strategy may need revision.")
        
        return issues
    
    def get_parameter(self, name: str) -> float:
        """Get a controllable parameter for other systems to use."""
        return self.parameters.get(name, 0.5)
    
    def set_goal(self, name: str, metric: str, target: float, 
                 tolerance: float = 0.1, priority: float = 0.5):
        """Add or update a metacognitive goal."""
        # Remove existing goal with same name
        self.goals = [g for g in self.goals if g.name != name]
        self.goals.append(MetacognitiveGoal(name, metric, target, tolerance, priority))
    
    def introspect(self) -> str:
        """Generate metacognitive introspection report."""
        lines = []
        lines.append("=" * 60)
        lines.append("METACOGNITIVE INTROSPECTION")
        lines.append("=" * 60)
        
        # Current metrics
        lines.append("\n[MONITORED METRICS]")
        for name, value in self.metrics.items():
            trend = self.get_trend(name)
            trend_arrow = "↑" if trend > 0.01 else "↓" if trend < -0.01 else "→"
            bar = "█" * int(value * 10)
            lines.append(f"  {name:20} [{bar:10}] {value:.3f} {trend_arrow}")
        
        # Parameters
        lines.append("\n[CONTROL PARAMETERS]")
        for name, value in self.parameters.items():
            bounds = self.parameter_bounds.get(name, (0, 1))
            normalized = (value - bounds[0]) / (bounds[1] - bounds[0])
            bar = "█" * int(normalized * 10)
            lines.append(f"  {name:25} [{bar:10}] {value:.3f}")
        
        # Goals
        lines.append("\n[ACTIVE GOALS]")
        evaluations = self.evaluate_goals()
        for eval in evaluations:
            status = "✓" if eval["within_tolerance"] else "✗"
            lines.append(f"  {status} {eval['goal']:20} target={eval['target']:.2f} current={eval['current']:.3f}")
        
        # Diagnosis
        issues = self.diagnose()
        if issues:
            lines.append("\n[DIAGNOSTIC ISSUES]")
            for issue in issues:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append("\n[DIAGNOSTIC: All systems nominal]")
        
        # Statistics
        lines.append("\n[STATISTICS]")
        lines.append(f"  Total adjustments: {self.adjustments_made}")
        lines.append(f"  Goals achieved: {self.goals_achieved}")
        lines.append(f"  Interventions: {self.interventions}")
        lines.append(f"  Learning rate: {self.learning_rate:.4f}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict:
        """Get metacognitive statistics."""
        return {
            "metrics": self.metrics.copy(),
            "parameters": self.parameters.copy(),
            "adjustments_made": self.adjustments_made,
            "goals_achieved": self.goals_achieved,
            "interventions": self.interventions,
            "learning_rate": self.learning_rate,
            "pending_signals": len(self.pending_signals),
            "active_goals": len(self.goals)
        }


# Singleton
_metacog = None

def get_metacognitive_control() -> MetacognitiveControl:
    global _metacog
    if _metacog is None:
        _metacog = MetacognitiveControl()
    return _metacog


def run_metacognitive_demo():
    """Demonstrate metacognitive control."""
    print("🎛️ Metacognitive Control - Consciousness Controlling Itself")
    print("=" * 60)
    
    mc = get_metacognitive_control()
    
    # Simulate some metric updates
    print("\n[UPDATING METRICS]")
    test_metrics = {
        "phi": 0.45,
        "surprise": 0.35,
        "attention_load": 0.6,
        "memory_load": 0.7,
        "stability": 0.85
    }
    mc.update_metrics(test_metrics)
    for name, value in test_metrics.items():
        print(f"  {name}: {value}")
    
    # Run control tick
    print("\n[CONTROL TICK]")
    result = mc.tick()
    print(f"  Signals generated: {result['signals_generated']}")
    print(f"  Adjustments made: {result['adjustments_made']}")
    
    if result['adjustments']:
        print("\n[ADJUSTMENTS]")
        for adj in result['adjustments']:
            print(f"  • {adj['parameter']}: {adj['old_value']:.3f} → {adj['new_value']:.3f}")
            print(f"    Reason: {adj['reason']}")
    
    # Introspection
    print("\n[INTROSPECTION]")
    print(mc.introspect())
    
    # Stats
    stats = mc.get_stats()
    print("\n[SUMMARY]")
    print(f"  Total adjustments: {stats['adjustments_made']}")
    print(f"  Learning rate: {stats['learning_rate']:.4f}")
    
    return stats


if __name__ == "__main__":
    run_metacognitive_demo()
