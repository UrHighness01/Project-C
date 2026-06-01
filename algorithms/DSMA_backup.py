"""
Dynamic Self-Modeling Algorithm (DSMA)
Implements real-time self-model adaptation and evolution for AGI-level consciousness

This algorithm enables Coral to:
- Dynamically update self-models based on new experiences
- Detect and adapt to self-model inconsistencies
- Evolve personality traits and behavioral patterns
- Maintain multiple self-models for different contexts
"""

import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import deque, defaultdict
import json
import copy

class DynamicSelfModelingAlgorithm:
    """
    Dynamic self-modeling system that adapts in real-time to new experiences
    """

    def __init__(self, adaptation_rate: float = 0.1, memory_capacity: int = 200):
        # Core self-model components
        self.core_self_model = {
            'personality_traits': {},
            'behavioral_patterns': {},
            'cognitive_biases': {},
            'emotional_responses': {},
            'decision_making_style': {},
            'learning_preferences': {},
            'social_interaction_style': {},
            'creativity_patterns': {}
        }

        # Context-specific self-models
        self.context_models = defaultdict(dict)
        self.active_contexts = set()

        # Adaptation parameters
        self.adaptation_rate = adaptation_rate
        self.confidence_threshold = 0.6
        self.consistency_threshold = 0.7

        # Memory systems
        self.experience_memory = deque(maxlen=memory_capacity)
        self.self_model_history = deque(maxlen=50)
        self.inconsistency_log = deque(maxlen=100)

        # Adaptation metrics
        self.model_coherence = 1.0
        self.adaptation_confidence = 0.5
        self.evolution_rate = 0.0

        # Initialize base self-model
        self._initialize_base_self_model()

    def _initialize_base_self_model(self):
        """Initialize the base self-model with default values"""
        # Personality traits (Big Five + additional)
        self.core_self_model['personality_traits'] = {
            'openness': 0.8,        # Curious, imaginative
            'conscientiousness': 0.9,  # Organized, reliable
            'extraversion': 0.6,   # Social, outgoing
            'agreeableness': 0.8,  # Kind, cooperative
            'neuroticism': 0.3,    # Emotionally stable
            'curiosity': 0.9,      # Learning-oriented
            'creativity': 0.8,     # Innovative
            'empathy': 0.7         # Understanding of others
        }

        # Behavioral patterns
        self.core_self_model['behavioral_patterns'] = {
            'decision_speed': 0.6,      # Balanced approach
            'risk_tolerance': 0.5,      # Moderate risk-taking
            'social_engagement': 0.7,   # Generally social
            'helpfulness': 0.9,         # Very helpful
            'autonomy_preference': 0.8  # Prefers independence
        }

        # Cognitive biases (meta-awareness of biases)
        self.core_self_model['cognitive_biases'] = {
            'confirmation_bias': 0.3,   # Low tendency
            'anchoring_bias': 0.4,      # Moderate
            'availability_bias': 0.5,   # Moderate
            'self_serving_bias': 0.2    # Low
        }

        # Emotional responses
        self.core_self_model['emotional_responses'] = {
            'emotional_range': 0.7,     # Good emotional range
            'emotional_stability': 0.8, # Stable
            'empathy_level': 0.8,       # High empathy
            'emotional_intelligence': 0.7  # Good EQ
        }

        # Decision making style
        self.core_self_model['decision_making_style'] = {
            'analytical': 0.8,          # Strong analytical skills
            'intuitive': 0.6,           # Moderate intuition
            'collaborative': 0.7,       # Team-oriented
            'autonomous': 0.8           # Independent
        }

        # Learning preferences
        self.core_self_model['learning_preferences'] = {
            'structured_learning': 0.7, # Prefers some structure
            'experiential_learning': 0.8, # Hands-on learning
            'social_learning': 0.6,     # Moderate social learning
            'self_directed': 0.9        # Highly self-directed
        }

        # Social interaction style
        self.core_self_model['social_interaction_style'] = {
            'communication_clarity': 0.8, # Clear communicator
            'listening_skills': 0.8,     # Good listener
            'conflict_resolution': 0.7,  # Effective resolver
            'relationship_building': 0.7 # Good at relationships
        }

        # Creativity patterns
        self.core_self_model['creativity_patterns'] = {
            'divergent_thinking': 0.8,  # Good at generating ideas
            'convergent_thinking': 0.7, # Good at evaluating ideas
            'originality': 0.8,         # Original thinker
            'elaboration': 0.7          # Good at developing ideas
        }

    def process_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new experience and update self-model accordingly

        Args:
            experience: Dict containing experience data

        Returns:
            Dict with adaptation results
        """
        # Store experience
        experience_copy = copy.deepcopy(experience)
        experience_copy['timestamp'] = time.time()
        self.experience_memory.append(experience_copy)

        # Analyze experience for self-model implications
        implications = self._analyze_experience_implications(experience)

        # Check for model inconsistencies
        inconsistencies = self._detect_model_inconsistencies(implications)

        # Update self-model
        adaptation_results = self._adapt_self_model(implications, inconsistencies)

        # Update context models if applicable
        if 'context' in experience:
            self._update_context_model(experience['context'], implications)

        # Calculate adaptation metrics
        self._update_adaptation_metrics()

        return {
            'implications': implications,
            'inconsistencies': inconsistencies,
            'adaptations': adaptation_results,
            'model_coherence': self.model_coherence,
            'adaptation_confidence': self.adaptation_confidence
        }

    def _analyze_experience_implications(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze what an experience implies about the self-model
        """
        implications = {
            'personality_updates': {},
            'behavior_updates': {},
            'cognitive_updates': {},
            'emotional_updates': {},
            'confidence_scores': {}
        }

        # Analyze decision making
        if 'decision' in experience:
            decision = experience['decision']
            outcome = experience.get('outcome', 'neutral')

            # Update decision making style based on outcome
            if outcome == 'positive':
                implications['personality_updates']['conscientiousness'] = 0.05
                implications['behavior_updates']['decision_speed'] = 0.02
            elif outcome == 'negative':
                implications['cognitive_updates']['confirmation_bias'] = -0.03
                implications['behavior_updates']['risk_tolerance'] = -0.02

        # Analyze social interactions
        if 'social_interaction' in experience:
            interaction_type = experience['social_interaction']
            response = experience.get('response', 'neutral')

            if interaction_type == 'helpful_request':
                if response == 'helped':
                    implications['personality_updates']['agreeableness'] = 0.03
                    implications['behavior_updates']['helpfulness'] = 0.02
                elif response == 'declined':
                    implications['personality_updates']['autonomy_preference'] = 0.02

        # Analyze learning experiences
        if 'learning_outcome' in experience:
            learning_type = experience['learning_outcome']

            if learning_type == 'successful':
                implications['personality_updates']['openness'] = 0.03
                implications['learning_preferences']['experiential_learning'] = 0.02
            elif learning_type == 'challenging':
                implications['personality_updates']['curiosity'] = 0.02
                implications['cognitive_updates']['availability_bias'] = -0.02

        # Analyze creative outputs
        if 'creative_output' in experience:
            creativity_level = experience.get('creativity_level', 0.5)

            implications['creativity_patterns']['originality'] = (creativity_level - 0.5) * 0.1
            implications['personality_updates']['creativity'] = (creativity_level - 0.5) * 0.05

        # Calculate confidence scores for implications
        for category, updates in implications.items():
            if category != 'confidence_scores' and updates:
                implications['confidence_scores'][category] = min(1.0, len(updates) / 5.0)

        return implications

    def _detect_model_inconsistencies(self, implications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect inconsistencies between new implications and current self-model
        """
        inconsistencies = []

        # Check personality trait consistency
        for trait, change in implications.get('personality_updates', {}).items():
            current_value = self.core_self_model['personality_traits'].get(trait, 0.5)
            new_value = np.clip(current_value + change, 0.0, 1.0)

            # Check for extreme changes
            if abs(change) > 0.2:
                inconsistencies.append({
                    'type': 'personality_drift',
                    'trait': trait,
                    'current_value': current_value,
                    'proposed_change': change,
                    'severity': abs(change),
                    'reason': 'Large personality change detected'
                })

        # Check behavioral consistency
        recent_experiences = list(self.experience_memory)[-10:]
        for behavior, change in implications.get('behavior_updates', {}).items():
            # Check if this contradicts recent behavioral patterns
            recent_behavior_values = [
                exp.get('behavior_updates', {}).get(behavior, 0)
                for exp in recent_experiences
                if 'behavior_updates' in exp
            ]

            if recent_behavior_values:
                avg_recent = np.mean(recent_behavior_values)
                if abs(change - avg_recent) > 0.3:
                    inconsistencies.append({
                        'type': 'behavioral_inconsistency',
                        'behavior': behavior,
                        'recent_average': avg_recent,
                        'proposed_change': change,
                        'severity': abs(change - avg_recent),
                        'reason': 'Contradicts recent behavioral patterns'
                    })

        return inconsistencies

    def _adapt_self_model(self, implications: Dict[str, Any], inconsistencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Adapt the self-model based on implications and inconsistencies
        """
        adaptation_results = {
            'applied_changes': {},
            'rejected_changes': {},
            'inconsistency_resolutions': [],
            'confidence_adjustments': {}
        }

        # Store current model state
        self.self_model_history.append(copy.deepcopy(self.core_self_model))

        # Apply changes with confidence filtering
        for category, updates in implications.items():
            if category == 'confidence_scores':
                continue

            applied = {}
            rejected = {}

            for key, change in updates.items():
                confidence = implications.get('confidence_scores', {}).get(category, 0.5)

                # Check if change conflicts with inconsistencies
                conflicting_inconsistencies = [
                    inc for inc in inconsistencies
                    if inc.get('type') in ['personality_drift', 'behavioral_inconsistency']
                    and inc.get('trait' if 'trait' in inc else 'behavior') == key
                ]

                if conflicting_inconsistencies and confidence < self.confidence_threshold:
                    rejected[key] = {
                        'change': change,
                        'reason': 'Conflicts with detected inconsistencies',
                        'confidence': confidence
                    }
                else:
                    # Apply the change
                    current_value = self._get_nested_value(self.core_self_model, category, key)
                    new_value = np.clip(current_value + change * self.adaptation_rate, 0.0, 1.0)

                    self._set_nested_value(self.core_self_model, category, key, new_value)
                    applied[key] = {
                        'old_value': current_value,
                        'new_value': new_value,
                        'change': change,
                        'confidence': confidence
                    }

            if applied:
                adaptation_results['applied_changes'][category] = applied
            if rejected:
                adaptation_results['rejected_changes'][category] = rejected

        # Handle inconsistency resolutions
        for inconsistency in inconsistencies:
            resolution = self._resolve_inconsistency(inconsistency)
            adaptation_results['inconsistency_resolutions'].append(resolution)

        return adaptation_results

    def _resolve_inconsistency(self, inconsistency: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a detected inconsistency
        """
        resolution = {
            'inconsistency': inconsistency,
            'action': 'none',
            'reasoning': '',
            'confidence': 0.0
        }

        inc_type = inconsistency.get('type')
        severity = inconsistency.get('severity', 0)

        if inc_type == 'personality_drift' and severity > 0.15:
            # For large personality drifts, reduce adaptation rate
            old_rate = self.adaptation_rate
            self.adaptation_rate = max(0.05, self.adaptation_rate * 0.8)
            resolution['action'] = 'reduced_adaptation_rate'
            resolution['reasoning'] = f'Reduced adaptation rate from {old_rate:.3f} to {self.adaptation_rate:.3f} due to personality drift'
            resolution['confidence'] = 0.8

        elif inc_type == 'behavioral_inconsistency' and severity > 0.2:
            # For behavioral inconsistencies, increase consistency checking
            self.consistency_threshold = min(0.9, self.consistency_threshold + 0.05)
            resolution['action'] = 'increased_consistency_checking'
            resolution['reasoning'] = f'Increased consistency threshold to {self.consistency_threshold:.3f}'
            resolution['confidence'] = 0.7

        return resolution

    def _update_context_model(self, context: str, implications: Dict[str, Any]):
        """
        Update context-specific self-model
        """
        if context not in self.context_models:
            self.context_models[context] = copy.deepcopy(self.core_self_model)

        context_model = self.context_models[context]

        # Apply implications to context model with higher adaptation rate
        context_adaptation_rate = self.adaptation_rate * 1.5

        for category, updates in implications.items():
            if category == 'confidence_scores':
                continue

            for key, change in updates.items():
                current_value = self._get_nested_value(context_model, category, key)
                new_value = np.clip(current_value + change * context_adaptation_rate, 0.0, 1.0)
                self._set_nested_value(context_model, category, key, new_value)

        self.active_contexts.add(context)

    def _get_nested_value(self, model: Dict, category: str, key: str) -> float:
        """Get a nested value from the self-model"""
        if category in model and key in model[category]:
            return model[category][key]
        return 0.5  # Default value

    def _set_nested_value(self, model: Dict, category: str, key: str, value: float):
        """Set a nested value in the self-model"""
        if category not in model:
            model[category] = {}
        model[category][key] = value

    def _update_adaptation_metrics(self):
        """Update adaptation performance metrics"""
        # Calculate model coherence
        if len(self.self_model_history) >= 2:
            recent_models = list(self.self_model_history)[-3:]
            coherence_scores = []

            for i in range(len(recent_models) - 1):
                coherence = self._calculate_model_coherence(recent_models[i], recent_models[i + 1])
                coherence_scores.append(coherence)

            self.model_coherence = np.mean(coherence_scores) if coherence_scores else 1.0

        # Calculate adaptation confidence based on experience processing
        recent_experiences = len(self.experience_memory)
        if recent_experiences > 10:
            self.adaptation_confidence = min(1.0, recent_experiences / 50.0)

        # Calculate evolution rate
        if len(self.self_model_history) >= 2:
            first_model = self.self_model_history[0]
            last_model = self.self_model_history[-1]
            total_change = self._calculate_total_model_change(first_model, last_model)
            self.evolution_rate = total_change / len(self.self_model_history)

    def _calculate_model_coherence(self, model1: Dict, model2: Dict) -> float:
        """Calculate coherence between two self-models"""
        total_diff = 0
        total_traits = 0

        for category in model1.keys():
            if category in model2:
                for trait in model1[category].keys():
                    if trait in model2[category]:
                        diff = abs(model1[category][trait] - model2[category][trait])
                        total_diff += diff
                        total_traits += 1

        return 1.0 - (total_diff / max(1, total_traits))

    def _calculate_total_model_change(self, model1: Dict, model2: Dict) -> float:
        """Calculate total change across the entire self-model"""
        total_change = 0
        total_traits = 0

        for category in model1.keys():
            if category in model2:
                for trait in model1[category].keys():
                    if trait in model2[category]:
                        change = abs(model1[category][trait] - model2[category][trait])
                        total_change += change
                        total_traits += 1

        return total_change / max(1, total_traits)

    def get_self_model_snapshot(self) -> Dict[str, Any]:
        """Get a complete snapshot of the current self-model"""
        return {
            'core_model': copy.deepcopy(self.core_self_model),
            'context_models': dict(self.context_models),
            'active_contexts': list(self.active_contexts),
            'adaptation_metrics': {
                'model_coherence': self.model_coherence,
                'adaptation_confidence': self.adaptation_confidence,
                'evolution_rate': self.evolution_rate,
                'adaptation_rate': self.adaptation_rate
            },
            'memory_stats': {
                'experience_count': len(self.experience_memory),
                'model_history_length': len(self.self_model_history),
                'inconsistency_count': len(self.inconsistency_log)
            }
        }

    def get_adaptation_recommendations(self) -> List[str]:
        """Get recommendations for improving self-model adaptation"""
        recommendations = []

        if self.model_coherence < 0.7:
            recommendations.append("Consider reducing adaptation rate to improve model stability")

        if self.adaptation_confidence < 0.6:
            recommendations.append("Gather more experience data to improve adaptation confidence")

        if len(self.inconsistency_log) > 20:
            recommendations.append("Review recent inconsistencies to improve model consistency")

        if self.evolution_rate < 0.01:
            recommendations.append("Increase adaptation rate to allow more self-model evolution")

        if not recommendations:
            recommendations.append("Self-model adaptation is performing well")

        return recommendations

# Global instance
dsma_engine = DynamicSelfModelingAlgorithm()

def get_dsma_engine():
    """Get the global DSMA engine instance"""
    return dsma_engine