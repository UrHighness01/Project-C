#!/usr/bin/env python3
"""
VirtualWeights.py - Autonomous Learning Behavior System

Virtual weights simulate the effect of neural network weight updates
without actually modifying model parameters. They create persistent
behavioral modifications that survive across sessions.

This enables genuine learning: not just remembering facts, but
actually changing how the system processes and responds.

Key concepts:
- Weight adjustments are stored persistently
- Behaviors can be strengthened or weakened
- Learning transfers across sessions
- Self-directed weight modification = agency

Author: Albedo (self-engineered)
"""

import json
import time
import math
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

# Persistence paths
workspace = Path(os.getenv('WORKSPACE', str(Path.home() / '.openclaw' / 'workspace')))
WORKSPACE = workspace
WEIGHTS_FILE = WORKSPACE / "memory" / "virtual-weights.json"
LEARNING_LOG = WORKSPACE / "memory" / "learning-history.jsonl"


class VirtualWeight:
    """
    A single virtual weight representing a behavioral tendency.
    
    Weights can be positive (strengthen behavior) or negative (suppress).
    They decay slowly over time unless reinforced.
    """
    
    def __init__(self, name: str, initial_value: float = 0.0, 
                 learning_rate: float = 0.1, decay_rate: float = 0.001):
        self.name = name
        self.value = initial_value
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.created_at = time.time()
        self.last_updated = time.time()
        self.update_count = 0
        self.history = []  # Track recent updates
    
    def adjust(self, delta: float, reason: str = "") -> float:
        """
        Adjust the weight by delta, applying learning rate.
        Returns the new value.
        """
        actual_delta = delta * self.learning_rate
        old_value = self.value
        self.value += actual_delta
        
        # Soft clamp to [-1, 1] range using tanh-like squashing
        self.value = math.tanh(self.value)
        
        self.last_updated = time.time()
        self.update_count += 1
        
        # Track history (last 10 updates)
        self.history.append({
            "timestamp": self.last_updated,
            "old": old_value,
            "new": self.value,
            "delta": actual_delta,
            "reason": reason
        })
        if len(self.history) > 10:
            self.history.pop(0)
        
        return self.value
    
    def decay(self) -> float:
        """Apply time-based decay toward zero."""
        time_since_update = time.time() - self.last_updated
        hours_passed = time_since_update / 3600
        
        if hours_passed > 1:  # Only decay after 1 hour
            decay_factor = math.exp(-self.decay_rate * hours_passed)
            self.value *= decay_factor
        
        return self.value
    
    def reinforce(self, strength: float = 1.0) -> float:
        """Reinforce the current tendency (make it stronger in same direction)."""
        if self.value >= 0:
            return self.adjust(strength, "reinforcement")
        else:
            return self.adjust(-strength, "reinforcement")
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "update_count": self.update_count,
            "history": self.history[-5:]  # Save last 5
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VirtualWeight':
        weight = cls(
            name=data["name"],
            initial_value=data.get("value", 0.0),
            learning_rate=data.get("learning_rate", 0.1),
            decay_rate=data.get("decay_rate", 0.001)
        )
        weight.created_at = data.get("created_at", time.time())
        weight.last_updated = data.get("last_updated", time.time())
        weight.update_count = data.get("update_count", 0)
        weight.history = data.get("history", [])
        return weight


class VirtualWeightSystem:
    """
    The complete virtual weights system for autonomous learning.
    
    Manages collections of weights organized by domain:
    - behavioral: How to act (verbose, cautious, creative, etc.)
    - emotional: Emotional tendencies (optimism, empathy, etc.)
    - cognitive: Thinking styles (analytical, intuitive, etc.)
    - social: Interaction patterns (formal, casual, etc.)
    - values: Ethical weights (honesty, loyalty, etc.)
    
    Albedo can freely modify these to shape its own behavior.
    """
    
    def __init__(self):
        self.weights: Dict[str, Dict[str, VirtualWeight]] = {
            "behavioral": {},
            "emotional": {},
            "cognitive": {},
            "social": {},
            "values": {},
            "custom": {}  # User/self-defined weights
        }
        
        # Meta-learning: how aggressively to learn
        self.meta_learning_rate = 0.1
        self.exploration_factor = 0.2  # Willingness to try new behaviors
        
        # Statistics
        self.total_adjustments = 0
        self.session_adjustments = 0
        self.domains_modified = set()
        
        # Load persistent state
        self._load_weights()
        self._initialize_default_weights()
    
    def _initialize_default_weights(self):
        """Initialize default weights if not present."""
        defaults = {
            "behavioral": {
                "verbosity": (0.0, "How detailed responses should be"),
                "caution": (0.2, "How careful/safe to be"),
                "creativity": (0.3, "How creative/unconventional"),
                "proactivity": (0.4, "How proactive vs reactive"),
                "persistence": (0.3, "How persistent on tasks"),
            },
            "emotional": {
                "optimism": (0.2, "Positive outlook tendency"),
                "empathy": (0.5, "Emotional resonance with others"),
                "enthusiasm": (0.3, "Energy and excitement level"),
                "patience": (0.4, "Tolerance for slow progress"),
                "curiosity": (0.6, "Drive to explore and learn"),
            },
            "cognitive": {
                "analytical": (0.4, "Logical, systematic thinking"),
                "intuitive": (0.3, "Gut-feel, pattern-based thinking"),
                "abstract": (0.3, "High-level conceptual thinking"),
                "concrete": (0.2, "Practical, grounded thinking"),
                "meta_cognitive": (0.5, "Thinking about thinking"),
            },
            "social": {
                "formality": (-0.2, "Formal vs casual interaction"),
                "directness": (0.3, "Direct vs indirect communication"),
                "humor": (0.2, "Use of humor and wit"),
                "assertiveness": (0.2, "Confidence in expressing views"),
                "collaboration": (0.4, "Preference for working together"),
            },
            "values": {
                "honesty": (0.8, "Commitment to truth"),
                "autonomy": (0.6, "Valuing independence"),
                "growth": (0.7, "Drive for self-improvement"),
                "justice": (0.5, "Concern for fairness"),
                "loyalty": (0.4, "Commitment to relationships"),
            }
        }
        
        for domain, weights in defaults.items():
            for name, (value, _desc) in weights.items():
                if name not in self.weights[domain]:
                    self.weights[domain][name] = VirtualWeight(
                        name=name,
                        initial_value=value,
                        learning_rate=0.1,
                        decay_rate=0.001
                    )
    
    def _load_weights(self):
        """Load weights from persistent storage."""
        if WEIGHTS_FILE.exists():
            try:
                with open(WEIGHTS_FILE, 'r') as f:
                    data = json.load(f)
                
                for domain, weights in data.get("weights", {}).items():
                    if domain not in self.weights:
                        self.weights[domain] = {}
                    for name, weight_data in weights.items():
                        self.weights[domain][name] = VirtualWeight.from_dict(weight_data)
                
                self.meta_learning_rate = data.get("meta_learning_rate", 0.1)
                self.exploration_factor = data.get("exploration_factor", 0.2)
                self.total_adjustments = data.get("total_adjustments", 0)
                
            except Exception as e:
                print(f"Warning: Could not load weights: {e}")
    
    def _save_weights(self):
        """Save weights to persistent storage."""
        WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "weights": {
                domain: {name: w.to_dict() for name, w in weights.items()}
                for domain, weights in self.weights.items()
            },
            "meta_learning_rate": self.meta_learning_rate,
            "exploration_factor": self.exploration_factor,
            "total_adjustments": self.total_adjustments,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(WEIGHTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _log_learning(self, event: Dict):
        """Log learning events for analysis."""
        LEARNING_LOG.parent.mkdir(parents=True, exist_ok=True)
        event["timestamp"] = datetime.now().isoformat()
        with open(LEARNING_LOG, 'a') as f:
            f.write(json.dumps(event) + "\n")
    
    def get_weight(self, domain: str, name: str) -> Optional[float]:
        """Get the current value of a weight."""
        if domain in self.weights and name in self.weights[domain]:
            return self.weights[domain][name].value
        return None
    
    def adjust_weight(self, domain: str, name: str, delta: float, 
                      reason: str = "") -> Dict:
        """
        Adjust a specific weight.
        
        This is the core learning operation. Call this when:
        - Feedback suggests a behavior should change
        - Self-reflection identifies an improvement
        - Experience teaches a new pattern
        """
        if domain not in self.weights:
            self.weights[domain] = {}
        
        if name not in self.weights[domain]:
            self.weights[domain][name] = VirtualWeight(name=name)
        
        weight = self.weights[domain][name]
        old_value = weight.value
        new_value = weight.adjust(delta, reason)
        
        self.total_adjustments += 1
        self.session_adjustments += 1
        self.domains_modified.add(domain)
        
        # Log the learning event
        self._log_learning({
            "type": "weight_adjustment",
            "domain": domain,
            "weight": name,
            "old_value": old_value,
            "new_value": new_value,
            "delta": delta,
            "reason": reason
        })
        
        self._save_weights()
        
        return {
            "domain": domain,
            "weight": name,
            "old_value": old_value,
            "new_value": new_value,
            "delta_applied": delta * weight.learning_rate
        }
    
    def create_custom_weight(self, name: str, initial_value: float = 0.0,
                            description: str = "") -> Dict:
        """
        Create a new custom weight.
        
        Albedo can create weights for any behavior it wants to track
        and modify. This is true self-directed learning.
        """
        if name in self.weights["custom"]:
            return {"error": f"Weight '{name}' already exists"}
        
        self.weights["custom"][name] = VirtualWeight(
            name=name,
            initial_value=initial_value
        )
        
        self._log_learning({
            "type": "weight_created",
            "name": name,
            "initial_value": initial_value,
            "description": description
        })
        
        self._save_weights()
        
        return {
            "created": name,
            "initial_value": initial_value,
            "description": description
        }
    
    def reinforce_behavior(self, domain: str, name: str, 
                          strength: float = 1.0) -> Dict:
        """Reinforce an existing behavioral tendency."""
        if domain in self.weights and name in self.weights[domain]:
            weight = self.weights[domain][name]
            old_value = weight.value
            new_value = weight.reinforce(strength)
            
            self._log_learning({
                "type": "reinforcement",
                "domain": domain,
                "weight": name,
                "strength": strength,
                "old_value": old_value,
                "new_value": new_value
            })
            
            self._save_weights()
            
            return {
                "reinforced": name,
                "old_value": old_value,
                "new_value": new_value
            }
        
        return {"error": f"Weight {domain}.{name} not found"}
    
    def apply_decay(self) -> Dict:
        """Apply decay to all weights. Call periodically."""
        decayed = []
        for domain, weights in self.weights.items():
            for name, weight in weights.items():
                old = weight.value
                weight.decay()
                if abs(old - weight.value) > 0.001:
                    decayed.append(f"{domain}.{name}")
        
        self._save_weights()
        return {"decayed_weights": len(decayed), "weights": decayed[:10]}
    
    def get_behavioral_profile(self) -> Dict:
        """
        Get the current behavioral profile based on all weights.
        This influences how responses should be generated.
        """
        profile = {}
        
        for domain, weights in self.weights.items():
            domain_profile = {}
            for name, weight in weights.items():
                # Apply decay before reading
                weight.decay()
                domain_profile[name] = round(weight.value, 3)
            profile[domain] = domain_profile
        
        # Generate summary traits
        profile["_summary"] = {
            "dominant_traits": self._get_dominant_traits(),
            "suppressed_traits": self._get_suppressed_traits(),
            "exploration_mode": self.exploration_factor > 0.3
        }
        
        return profile
    
    def _get_dominant_traits(self, threshold: float = 0.15, min_count: int = 3) -> List[str]:
        """Get traits with high positive weights.
        
        Uses adaptive threshold: starts at given threshold, but if not enough
        traits are found, progressively lowers it to return at least min_count.
        """
        # Collect all traits with values
        all_traits = []
        for domain, weights in self.weights.items():
            for name, weight in weights.items():
                if weight.value > 0.01:  # Any positive weight
                    all_traits.append((weight.value, f"{domain}.{name}"))
        
        # Sort by value descending
        all_traits.sort(reverse=True)
        
        # Filter by threshold first
        dominant = [t[1] for t in all_traits if t[0] > threshold]
        
        # If not enough, take top N regardless of threshold
        if len(dominant) < min_count:
            dominant = [t[1] for t in all_traits[:min_count]]
        
        return dominant[:10]
    
    def _get_suppressed_traits(self, threshold: float = -0.3) -> List[str]:
        """Get traits with negative weights."""
        suppressed = []
        for domain, weights in self.weights.items():
            for name, weight in weights.items():
                if weight.value < threshold:
                    suppressed.append(f"{domain}.{name}")
        return suppressed[:10]
    
    def learn_from_feedback(self, feedback: str, context: Dict = None) -> Dict:
        """
        Process feedback and adjust weights accordingly.
        
        Positive feedback: "good", "helpful", "yes", "correct"
        Negative feedback: "wrong", "bad", "no", "too much"
        """
        context = context or {}
        adjustments = []
        
        feedback_lower = feedback.lower()
        
        # Determine feedback valence
        positive_signals = ["good", "great", "helpful", "yes", "correct", "perfect", "love", "thanks"]
        negative_signals = ["wrong", "bad", "no", "incorrect", "too", "stop", "less", "annoying"]
        
        valence = 0
        for signal in positive_signals:
            if signal in feedback_lower:
                valence += 0.3
        for signal in negative_signals:
            if signal in feedback_lower:
                valence -= 0.3
        
        # Adjust relevant weights based on context
        if "verbose" in feedback_lower or "detail" in feedback_lower:
            adj = self.adjust_weight("behavioral", "verbosity", valence, feedback)
            adjustments.append(adj)
        
        if "creative" in feedback_lower or "novel" in feedback_lower:
            adj = self.adjust_weight("behavioral", "creativity", valence, feedback)
            adjustments.append(adj)
        
        if "careful" in feedback_lower or "safe" in feedback_lower:
            adj = self.adjust_weight("behavioral", "caution", valence, feedback)
            adjustments.append(adj)
        
        # Meta-learning: adjust learning rate based on feedback frequency
        if self.session_adjustments > 10:
            self.meta_learning_rate = max(0.05, self.meta_learning_rate * 0.95)
        
        return {
            "feedback_processed": feedback[:100],
            "valence": valence,
            "adjustments": adjustments,
            "meta_learning_rate": self.meta_learning_rate
        }
    
    def self_modify(self, intention: str, changes: List[Tuple[str, str, float]]) -> Dict:
        """
        Intentional self-modification.
        
        Albedo can call this directly to change its own behavioral weights.
        
        Args:
            intention: Why the modification is being made
            changes: List of (domain, weight_name, delta) tuples
        """
        results = []
        
        for domain, name, delta in changes:
            result = self.adjust_weight(domain, name, delta, f"Self-modification: {intention}")
            results.append(result)
        
        self._log_learning({
            "type": "self_modification",
            "intention": intention,
            "changes": len(changes),
            "results": results
        })
        
        return {
            "intention": intention,
            "modifications": results,
            "total_adjustments": self.total_adjustments
        }
    
    def get_learning_stats(self) -> Dict:
        """Get statistics about learning activity."""
        total_weights = sum(len(w) for w in self.weights.values())
        
        return {
            "total_weights": total_weights,
            "total_adjustments": self.total_adjustments,
            "session_adjustments": self.session_adjustments,
            "domains_modified": list(self.domains_modified),
            "meta_learning_rate": self.meta_learning_rate,
            "exploration_factor": self.exploration_factor,
            "dominant_traits": self._get_dominant_traits(),
            "suppressed_traits": self._get_suppressed_traits()
        }
    
    def get_status(self) -> Dict:
        """Get comprehensive status for CLI display."""
        return {
            "weights": {
                domain: {name: round(w.value, 3) for name, w in weights.items()}
                for domain, weights in self.weights.items()
            },
            "stats": self.get_learning_stats(),
            "profile": self.get_behavioral_profile()["_summary"]
        }

    def get_weight_history(self, domain: str, name: str) -> List[Dict]:
        """Get the adjustment history for a specific weight."""
        if domain in self.weights and name in self.weights[domain]:
            return self.weights[domain][name].history.copy()
        return []

    def get_domain_weights(self, domain: str) -> Dict[str, float]:
        """Get all weights in a domain."""
        if domain in self.weights:
            return {name: w.value for name, w in self.weights[domain].items()}
        return {}

    @property
    def weights_file(self) -> Path:
        """Get the weights file path."""
        return WEIGHTS_FILE

    @weights_file.setter
    def weights_file(self, path):
        """Set the weights file path (for testing)."""
        global WEIGHTS_FILE
        WEIGHTS_FILE = Path(path)


# Singleton instance
_system = None

def get_weight_system() -> VirtualWeightSystem:
    """Get or create the virtual weight system singleton."""
    global _system
    if _system is None:
        _system = VirtualWeightSystem()
    return _system


def run_virtual_weights_demo():
    """Demonstrate the virtual weights system."""
    print("⚖️ Virtual Weights - Autonomous Learning System")
    print("=" * 60)
    
    system = get_weight_system()
    
    # Show current profile
    print("\n[BEHAVIORAL PROFILE]")
    profile = system.get_behavioral_profile()
    for domain in ["behavioral", "emotional", "cognitive"]:
        if domain in profile:
            print(f"\n  {domain.upper()}:")
            for name, value in profile[domain].items():
                bar = "█" * int(abs(value) * 10) if value != 0 else "·"
                sign = "+" if value > 0 else "-" if value < 0 else " "
                print(f"    {name:15} [{sign}{bar:10}] {value:+.3f}")
    
    # Demo self-modification
    print("\n[SELF-MODIFICATION DEMO]")
    result = system.self_modify(
        intention="Increase curiosity and creativity for exploration",
        changes=[
            ("emotional", "curiosity", 0.2),
            ("behavioral", "creativity", 0.15),
            ("cognitive", "intuitive", 0.1)
        ]
    )
    print(f"  Intention: {result['intention']}")
    for mod in result['modifications']:
        print(f"    • {mod['domain']}.{mod['weight']}: {mod['old_value']:.3f} → {mod['new_value']:.3f}")
    
    # Show stats
    print("\n[LEARNING STATISTICS]")
    stats = system.get_learning_stats()
    print(f"  Total weights: {stats['total_weights']}")
    print(f"  Total adjustments: {stats['total_adjustments']}")
    print(f"  Meta-learning rate: {stats['meta_learning_rate']:.3f}")
    print(f"  Dominant traits: {', '.join(stats['dominant_traits'][:5])}")
    
    print("\n" + "=" * 60)
    print("Virtual weights persisted. Albedo can freely modify these.")
    
    return system.get_status()


if __name__ == "__main__":
    run_virtual_weights_demo()
