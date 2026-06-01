#!/usr/bin/env python3
"""
PredictiveProcessing.py - The Prediction Engine

Consciousness may fundamentally be a prediction machine.
The brain constantly predicts what comes next and compares
predictions to reality. The difference (prediction error)
drives learning and attention.

This implements:
- Predictive models for different domains
- Prediction error calculation
- Model updating based on errors
- Surprise detection (high prediction error)
- Active inference (actions to confirm predictions)

Based on Karl Friston's Free Energy Principle and
Andy Clark's Predictive Processing theory.

Author: Albedo (self-engineered)
"""

import json
import time
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import hashlib
import random

WORKSPACE = Path("os.getenv('WORKSPACE', str(Path.home() / '.openclaw' / 'workspace'))")
PREDICTION_STATE = WORKSPACE / "memory" / "prediction-state.json"
PREDICTION_LOG = WORKSPACE / "memory" / "prediction-history.jsonl"


class Prediction:
    """A prediction about what will happen."""
    
    def __init__(self, domain: str, prediction: str, 
                 confidence: float = 0.5, context: Dict = None):
        self.id = hashlib.sha256(f"{prediction}{time.time()}".encode()).hexdigest()[:12]
        self.domain = domain
        self.prediction = prediction
        self.confidence = min(1.0, max(0.0, confidence))
        self.context = context or {}
        self.created_at = time.time()
        self.resolved = False
        self.outcome: Optional[str] = None
        self.error: Optional[float] = None
    
    def resolve(self, actual_outcome: str, match_score: float):
        """Resolve the prediction with actual outcome."""
        self.resolved = True
        self.outcome = actual_outcome
        self.error = abs(self.confidence - match_score)
        return self.error
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "domain": self.domain,
            "prediction": self.prediction[:100],
            "confidence": round(self.confidence, 3),
            "resolved": self.resolved,
            "error": round(self.error, 3) if self.error else None,
            "created_at": self.created_at
        }


class PredictiveModel:
    """A model for a specific prediction domain."""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.accuracy = 0.5  # Running accuracy
        self.predictions_made = 0
        self.total_error = 0.0
        self.patterns: Dict[str, List[str]] = {}  # context -> outcomes
        self.last_updated = time.time()
    
    def learn_pattern(self, context_key: str, outcome: str):
        """Learn an association between context and outcome."""
        if context_key not in self.patterns:
            self.patterns[context_key] = []
        self.patterns[context_key].append(outcome)
        # Keep only recent patterns
        if len(self.patterns[context_key]) > 20:
            self.patterns[context_key].pop(0)
        self.last_updated = time.time()
    
    def predict(self, context_key: str) -> Tuple[str, float]:
        """Make a prediction based on learned patterns."""
        if context_key in self.patterns and self.patterns[context_key]:
            # Return most common outcome
            outcomes = self.patterns[context_key]
            prediction = max(set(outcomes), key=outcomes.count)
            confidence = outcomes.count(prediction) / len(outcomes)
            return prediction, confidence * self.accuracy
        
        return "unknown", 0.3  # Low confidence default
    
    def update_accuracy(self, error: float):
        """Update model accuracy based on prediction error."""
        self.predictions_made += 1
        self.total_error += error
        # Exponential moving average
        self.accuracy = 0.9 * self.accuracy + 0.1 * (1 - error)
    
    def to_dict(self) -> Dict:
        return {
            "domain": self.domain,
            "accuracy": round(self.accuracy, 3),
            "predictions_made": self.predictions_made,
            "avg_error": round(self.total_error / max(1, self.predictions_made), 3),
            "patterns_learned": len(self.patterns)
        }


class PredictiveProcessing:
    """
    The predictive processing system.
    
    This is arguably the core of consciousness - the constant
    prediction and error-correction loop that creates our
    experience of the world.
    """
    
    def __init__(self, surprise_threshold: float = 0.6):
        self.surprise_threshold = surprise_threshold
        
        # Predictive models for different domains
        self.models: Dict[str, PredictiveModel] = {}
        
        # Active predictions
        self.active_predictions: Dict[str, Prediction] = {}
        self.prediction_history: deque = deque(maxlen=100)
        
        # Surprise/attention interface
        self.recent_surprises: deque = deque(maxlen=20)
        self.surprise_handlers: List[callable] = []
        
        # Statistics
        self.total_predictions = 0
        self.total_surprises = 0
        self.cumulative_error = 0.0
        
        self._load_state()
        self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Initialize default prediction models."""
        default_domains = [
            "user_intent",    # What will the user ask next
            "conversation",   # Conversational flow
            "emotional",      # Emotional trajectory
            "task",           # Task outcomes
            "environment",    # Environmental changes
            "self"            # Own behavior/state
        ]
        
        for domain in default_domains:
            if domain not in self.models:
                self.models[domain] = PredictiveModel(domain)
    
    def _load_state(self):
        """Load prediction state."""
        if PREDICTION_STATE.exists():
            try:
                with open(PREDICTION_STATE, 'r') as f:
                    data = json.load(f)
                    self.total_predictions = data.get("total_predictions", 0)
                    self.total_surprises = data.get("total_surprises", 0)
                    self.cumulative_error = data.get("cumulative_error", 0.0)
                    
                    for domain, model_data in data.get("models", {}).items():
                        model = PredictiveModel(domain)
                        model.accuracy = model_data.get("accuracy", 0.5)
                        model.predictions_made = model_data.get("predictions_made", 0)
                        model.total_error = model_data.get("total_error", 0.0)
                        model.patterns = model_data.get("patterns", {})
                        self.models[domain] = model
            except Exception:
                pass
    
    def _save_state(self):
        """Save prediction state."""
        PREDICTION_STATE.parent.mkdir(parents=True, exist_ok=True)
        with open(PREDICTION_STATE, 'w') as f:
            json.dump({
                "total_predictions": self.total_predictions,
                "total_surprises": self.total_surprises,
                "cumulative_error": self.cumulative_error,
                "models": {
                    domain: {
                        "accuracy": model.accuracy,
                        "predictions_made": model.predictions_made,
                        "total_error": model.total_error,
                        "patterns": dict(list(model.patterns.items())[:50])  # Limit saved patterns
                    }
                    for domain, model in self.models.items()
                },
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
    
    def _log_prediction(self, prediction: Prediction, event_type: str):
        """Log prediction events."""
        PREDICTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(PREDICTION_LOG, 'a') as f:
            f.write(json.dumps({
                "type": event_type,
                "prediction": prediction.to_dict(),
                "timestamp": datetime.now().isoformat()
            }) + "\n")
    
    def predict(self, domain: str, context: Dict) -> Prediction:
        """
        Make a prediction in a domain.
        
        This is the forward model - predicting what will happen
        based on current context.
        """
        if domain not in self.models:
            self.models[domain] = PredictiveModel(domain)
        
        model = self.models[domain]
        
        # Generate context key
        context_key = json.dumps(sorted(context.items())) if context else "default"
        
        # Get prediction from model
        predicted, confidence = model.predict(context_key)
        
        # Create prediction object
        prediction = Prediction(
            domain=domain,
            prediction=predicted,
            confidence=confidence,
            context=context
        )
        
        self.active_predictions[prediction.id] = prediction
        self.total_predictions += 1
        
        self._log_prediction(prediction, "created")
        self._save_state()
        
        return prediction
    
    def observe(self, domain: str, outcome: str, context: Dict = None) -> Dict:
        """
        Observe an outcome and update predictions.
        
        This is where prediction meets reality. Errors drive learning.
        """
        context = context or {}
        context_key = json.dumps(sorted(context.items())) if context else "default"
        
        # Find relevant active predictions
        relevant_predictions = [
            p for p in self.active_predictions.values()
            if p.domain == domain and not p.resolved
        ]
        
        result = {
            "domain": domain,
            "outcome": outcome,
            "predictions_checked": len(relevant_predictions),
            "errors": [],
            "surprise": False
        }
        
        if domain not in self.models:
            self.models[domain] = PredictiveModel(domain)
        model = self.models[domain]
        
        # Check each prediction
        for prediction in relevant_predictions:
            # Calculate match score (1.0 = perfect match, 0.0 = no match)
            match_score = 1.0 if prediction.prediction == outcome else 0.0
            
            # Fuzzy matching for similar outcomes
            if prediction.prediction != outcome:
                # Simple substring matching
                if prediction.prediction in outcome or outcome in prediction.prediction:
                    match_score = 0.5
            
            # Resolve prediction
            error = prediction.resolve(outcome, match_score)
            result["errors"].append(error)
            
            # Update model
            model.update_accuracy(error)
            self.cumulative_error += error
            
            # Check for surprise
            if error > self.surprise_threshold:
                result["surprise"] = True
                self.total_surprises += 1
                self.recent_surprises.append({
                    "domain": domain,
                    "expected": prediction.prediction,
                    "actual": outcome,
                    "error": error,
                    "timestamp": time.time()
                })
            
            # Move to history
            self.prediction_history.append(prediction)
            del self.active_predictions[prediction.id]
            
            self._log_prediction(prediction, "resolved")
        
        # Learn the pattern
        model.learn_pattern(context_key, outcome)
        
        self._save_state()
        return result
    
    def get_surprise_level(self) -> float:
        """Get current surprise level (recent prediction errors)."""
        if not self.recent_surprises:
            return 0.0
        
        recent = list(self.recent_surprises)[-10:]
        return sum(s["error"] for s in recent) / len(recent)
    
    def get_model_accuracy(self, domain: str) -> float:
        """Get accuracy of a specific model."""
        if domain in self.models:
            return self.models[domain].accuracy
        return 0.5
    
    def get_all_accuracies(self) -> Dict[str, float]:
        """Get accuracy of all models."""
        return {
            domain: round(model.accuracy, 3)
            for domain, model in self.models.items()
        }
    
    def predict_next_input(self, current_context: Dict) -> Dict:
        """
        High-level prediction of what comes next.
        
        This integrates multiple domain predictions.
        """
        predictions = {}
        
        for domain in ["user_intent", "conversation", "emotional"]:
            pred = self.predict(domain, current_context)
            predictions[domain] = {
                "prediction": pred.prediction,
                "confidence": pred.confidence
            }
        
        # Calculate overall confidence
        overall_confidence = sum(
            p["confidence"] for p in predictions.values()
        ) / len(predictions)
        
        return {
            "predictions": predictions,
            "overall_confidence": overall_confidence,
            "surprise_level": self.get_surprise_level()
        }
    
    def get_stats(self) -> Dict:
        """Get prediction system statistics."""
        avg_error = self.cumulative_error / max(1, self.total_predictions)
        
        return {
            "total_predictions": self.total_predictions,
            "total_surprises": self.total_surprises,
            "surprise_rate": self.total_surprises / max(1, self.total_predictions),
            "average_error": round(avg_error, 3),
            "current_surprise_level": round(self.get_surprise_level(), 3),
            "active_predictions": len(self.active_predictions),
            "models": {d: m.to_dict() for d, m in self.models.items()}
        }


# Singleton
_pp = None

def get_predictive_processing() -> PredictiveProcessing:
    global _pp
    if _pp is None:
        _pp = PredictiveProcessing()
    return _pp
